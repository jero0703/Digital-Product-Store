from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import func
from sqlalchemy.orm import Session,joinedload
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Order
from app.schemas import OrderPage,OrderResponse
from app.utils.pagination import page_meta
router=APIRouter(prefix="/orders",tags=["Orders"])

def serialize(o):
    return {"id":o.id,"total_amount":o.total_amount,"status":o.status,"created_at":o.created_at,"items":[{"id":i.id,"product_id":i.product_id,"product_name":i.product_name,"quantity":i.quantity,"unit_price":i.unit_price,"subtotal":i.subtotal} for i in o.items],"payment":o.payment}

@router.get("",response_model=OrderPage)
def list_orders(page:int=Query(1,ge=1),limit:int=Query(5,ge=1,le=100),user=Depends(get_current_user),db:Session=Depends(get_db)):
    q=db.query(Order).filter(Order.user_id==user.id)
    total=q.with_entities(func.count(Order.id)).scalar() or 0
    items=q.options(joinedload(Order.items),joinedload(Order.payment)).order_by(Order.id.desc()).offset((page-1)*limit).limit(limit).all()
    return {"items":[serialize(o) for o in items],**page_meta(total,page,limit)}

@router.get("/{order_id}",response_model=OrderResponse)
def get_order(order_id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    o=db.query(Order).options(joinedload(Order.items),joinedload(Order.payment)).filter(Order.id==order_id,Order.user_id==user.id).first()
    if not o: raise HTTPException(404,"Order not found")
    return serialize(o)
