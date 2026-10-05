import os
from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy.orm import Session,joinedload
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Cart,Order,Payment
from app.schemas import CheckoutSessionResponse
from app.services.order_service import create_order_from_cart,update_payment_from_success,update_payment_from_failure,clear_cart
from app.services.stripe_service import create_checkout_session,construct_webhook_event
router=APIRouter(prefix="/payments",tags=["Payments"])

@router.post("/create-checkout-session",response_model=CheckoutSessionResponse)
def checkout(user=Depends(get_current_user),db:Session=Depends(get_db)):
    try:
        order,payment,cart=create_order_from_cart(db,user.id)
        db.flush()
        session=create_checkout_session(order_id=order.id,user_email=user.email,items=order.items)
        payment.stripe_session_id=session.id
        db.commit()
        return {"order_id":order.id,"session_id":session.id,"checkout_url":session.url}
    except ValueError as e:
        db.rollback(); raise HTTPException(400,str(e))
    except Exception as e:
        db.rollback(); raise HTTPException(502,f"Stripe checkout failed: {e}")

@router.post("/webhook",status_code=200)
async def webhook(request:Request,db:Session=Depends(get_db)):
    payload=await request.body(); signature=request.headers.get("stripe-signature")
    secret=os.getenv("STRIPE_WEBHOOK_SECRET")
    if not signature or not secret: raise HTTPException(400,"Webhook signature is missing or not configured")
    try: event=construct_webhook_event(payload,signature,secret)
    except Exception: raise HTTPException(400,"Invalid webhook signature")
    event_id=event.get("id")
    event_type=event.get("type")
    data=event.get("data",{}).get("object",{})
    try:
        if event_type=="checkout.session.completed":
            session_id=data.get("id"); order_id=(data.get("metadata") or {}).get("order_id")
            if not order_id: return {"received":True}
            payment=db.query(Payment).options(joinedload(Payment.order)).filter(Payment.order_id==int(order_id)).first()
            if payment:
                update_payment_from_success(db,payment,session_id,data.get("payment_intent"));
                cart=db.query(Cart).filter(Cart.user_id==payment.order.user_id).options(joinedload(Cart.items)).first()
                if cart: clear_cart(db,cart)
        elif event_type=="payment_intent.payment_failed":
            intent_id=data.get("id")
            payment=db.query(Payment).options(joinedload(Payment.order)).filter(Payment.stripe_payment_intent_id==intent_id).first()
            if payment: update_payment_from_failure(payment,intent_id)
        db.commit(); return {"received":True,"event_id":event_id}
    except Exception:
        db.rollback(); raise HTTPException(500,"Webhook processing failed")
