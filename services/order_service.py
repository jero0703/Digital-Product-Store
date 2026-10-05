from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from app.models import Cart, CartItem, Order, OrderItem, Payment

def create_order_from_cart(db:Session,user_id:int):
    cart=db.query(Cart).options(joinedload(Cart.items).joinedload(CartItem.product)).filter(Cart.user_id==user_id).first()
    if not cart or not cart.items: raise ValueError("Cannot checkout with an empty cart")
    for item in cart.items:
        if not item.product or not item.product.is_active: raise ValueError(f"Product {item.product_id} is unavailable")
    total=sum((item.product.price*item.quantity for item in cart.items), Decimal("0.00"))
    order=Order(user_id=user_id,total_amount=total,status="PENDING")
    db.add(order); db.flush()
    for item in cart.items:
        db.add(OrderItem(order_id=order.id,product_id=item.product_id,product_name=item.product.name,quantity=item.quantity,unit_price=item.product.price,subtotal=item.product.price*item.quantity))
    payment=Payment(order_id=order.id,amount=total,currency="usd",status="PENDING")
    db.add(payment); db.flush()
    return order,payment,cart

def clear_cart(db:Session,cart:Cart):
    cart.items.clear()

def update_payment_from_success(db:Session,payment:Payment,session_id:str,payment_intent_id:str|None):
    if payment.status=="PAID": return
    payment.status="PAID"; payment.stripe_session_id=session_id; payment.stripe_payment_intent_id=payment_intent_id
    payment.order.status="PAID"

def update_payment_from_failure(payment:Payment,payment_intent_id:str|None=None):
    if payment.status=="PAID": return
    payment.status="FAILED"; payment.stripe_payment_intent_id=payment_intent_id; payment.order.status="FAILED"
