from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import func
from sqlalchemy.orm import Session,joinedload
from app.database import get_db
from app.dependencies import get_current_admin
from app.models import Product,Order,OrderItem,User
from app.schemas import ProductCreate,ProductUpdate,ProductResponse,OrderPage,AdminStatsResponse,PopularProductReport,OrdersPerUserReport,TopCustomerReport
from app.utils.pagination import page_meta
router=APIRouter(prefix="/admin",tags=["Admin"])

@router.get("/products",response_model=list[ProductResponse])
def admin_products(_:object=Depends(get_current_admin),db:Session=Depends(get_db)): return db.query(Product).order_by(Product.id.desc()).all()

@router.post("/products",response_model=ProductResponse,status_code=201)
def admin_create(data:ProductCreate,_:object=Depends(get_current_admin),db:Session=Depends(get_db)):
    p=Product(**data.model_dump()); db.add(p); db.commit(); db.refresh(p); return p

@router.put("/products/{product_id}",response_model=ProductResponse)
def admin_update(product_id:int,data:ProductUpdate,_:object=Depends(get_current_admin),db:Session=Depends(get_db)):
    p=db.query(Product).filter(Product.id==product_id).first()
    if not p: raise HTTPException(404,"Product not found")
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(p,k,v.strip() if isinstance(v,str) else v)
    db.commit(); db.refresh(p); return p

@router.delete("/products/{product_id}",status_code=204)
def admin_delete(product_id:int,_:object=Depends(get_current_admin),db:Session=Depends(get_db)):
    p=db.query(Product).filter(Product.id==product_id).first()
    if not p: raise HTTPException(404,"Product not found")
    p.is_active=False; db.commit()

@router.get("/orders",response_model=OrderPage)
def admin_orders(page:int=Query(1,ge=1),limit:int=Query(10,ge=1,le=100),_=Depends(get_current_admin),db:Session=Depends(get_db)):
    q=db.query(Order); total=q.with_entities(func.count(Order.id)).scalar() or 0
    orders=q.options(joinedload(Order.items),joinedload(Order.payment)).order_by(Order.id.desc()).offset((page-1)*limit).limit(limit).all()
    items=[]
    for o in orders: items.append({"id":o.id,"total_amount":o.total_amount,"status":o.status,"created_at":o.created_at,"items":[{"id":i.id,"product_id":i.product_id,"product_name":i.product_name,"quantity":i.quantity,"unit_price":i.unit_price,"subtotal":i.subtotal} for i in o.items],"payment":o.payment})
    return {"items":items,**page_meta(total,page,limit)}

@router.get("/stats",response_model=AdminStatsResponse)
def stats(_:object=Depends(get_current_admin),db:Session=Depends(get_db)):
    total_products=db.query(func.count(Product.id)).scalar() or 0
    total_orders=db.query(func.count(Order.id)).scalar() or 0
    paid_orders=db.query(func.count(Order.id)).filter(Order.status=="PAID").scalar() or 0
    failed_orders=db.query(func.count(Order.id)).filter(Order.status=="FAILED").scalar() or 0
    revenue=db.query(func.coalesce(func.sum(Order.total_amount),0)).filter(Order.status=="PAID").scalar() or 0
    return {"total_products":total_products,"total_orders":total_orders,"paid_orders":paid_orders,"failed_orders":failed_orders,"total_revenue":revenue}

@router.get("/reports/most-purchased-products",response_model=list[PopularProductReport])
def most_purchased(_:object=Depends(get_current_admin),db:Session=Depends(get_db)):
    rows=db.query(OrderItem.product_id,OrderItem.product_name,func.sum(OrderItem.quantity).label("quantity_sold"),func.sum(OrderItem.subtotal).label("revenue")).join(Order).filter(Order.status=="PAID").group_by(OrderItem.product_id,OrderItem.product_name).order_by(func.sum(OrderItem.quantity).desc()).all()
    return [{"product_id":r.product_id,"product_name":r.product_name,"quantity_sold":r.quantity_sold,"revenue":r.revenue} for r in rows]

@router.get("/reports/orders-per-user",response_model=list[OrdersPerUserReport])
def orders_per_user(_:object=Depends(get_current_admin),db:Session=Depends(get_db)):
    rows=db.query(User.id.label("user_id"),User.name.label("user_name"),func.count(Order.id).label("order_count")).join(Order,Order.user_id==User.id).group_by(User.id,User.name).order_by(func.count(Order.id).desc()).all()
    return [{"user_id":r.user_id,"user_name":r.user_name,"order_count":r.order_count} for r in rows]

@router.get("/reports/top-customers",response_model=list[TopCustomerReport])
def top_customers(_:object=Depends(get_current_admin),db:Session=Depends(get_db)):
    rows=db.query(User.id.label("user_id"),User.name.label("user_name"),func.sum(Order.total_amount).label("total_spent")).join(Order,Order.user_id==User.id).filter(Order.status=="PAID").group_by(User.id,User.name).order_by(func.sum(Order.total_amount).desc()).all()
    return [{"user_id":r.user_id,"user_name":r.user_name,"total_spent":r.total_spent} for r in rows]

@router.get("/reports/never-purchased-products",response_model=list[ProductResponse])
def never_purchased(_:object=Depends(get_current_admin),db:Session=Depends(get_db)):
    purchased=db.query(OrderItem.product_id).join(Order).filter(Order.status=="PAID",OrderItem.product_id.isnot(None)).distinct().subquery()
    return db.query(Product).filter(~Product.id.in_(purchased)).all()
