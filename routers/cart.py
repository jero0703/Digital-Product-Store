from decimal import Decimal
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session,joinedload
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Cart,CartItem,Product
from app.schemas import CartItemCreate,CartItemUpdate,CartResponse
router=APIRouter(prefix="/cart",tags=["Cart"])

def get_or_create_cart(db,user_id):
    cart=db.query(Cart).options(joinedload(Cart.items).joinedload(CartItem.product)).filter(Cart.user_id==user_id).first()
    if not cart:
        cart=Cart(user_id=user_id); db.add(cart); db.commit(); db.refresh(cart)
    return cart

def serialize(cart):
    items=[{"id":i.id,"product_id":i.product_id,"product_name":i.product.name,"quantity":i.quantity,"unit_price":i.product.price,"subtotal":i.product.price*i.quantity} for i in cart.items]
    return {"id":cart.id,"items":items,"total_amount":sum((x["subtotal"] for x in items),Decimal("0.00"))}

@router.get("",response_model=CartResponse)
def get_cart(user=Depends(get_current_user),db:Session=Depends(get_db)):
    return serialize(get_or_create_cart(db,user.id))

@router.post("/items",response_model=CartResponse,status_code=201)
def add_item(data:CartItemCreate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    product=db.query(Product).filter(Product.id==data.product_id).first()
    if not product or not product.is_active: raise HTTPException(404,"Active product not found")
    cart=get_or_create_cart(db,user.id)
    item=db.query(CartItem).filter(CartItem.cart_id==cart.id,CartItem.product_id==product.id).first()
    if item: item.quantity+=data.quantity
    else: db.add(CartItem(cart_id=cart.id,product_id=product.id,quantity=data.quantity))
    db.commit(); cart=get_or_create_cart(db,user.id); return serialize(cart)

@router.put("/items/{item_id}",response_model=CartResponse)
def update_item(item_id:int,data:CartItemUpdate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    item=db.query(CartItem).join(Cart).filter(CartItem.id==item_id,Cart.user_id==user.id).first()
    if not item: raise HTTPException(404,"Cart item not found")
    item.quantity=data.quantity; db.commit(); return serialize(get_or_create_cart(db,user.id))

@router.delete("/items/{item_id}",response_model=CartResponse)
def remove_item(item_id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    item=db.query(CartItem).join(Cart).filter(CartItem.id==item_id,Cart.user_id==user.id).first()
    if not item: raise HTTPException(404,"Cart item not found")
    db.delete(item); db.commit(); return serialize(get_or_create_cart(db,user.id))

@router.delete("",status_code=204)
def clear_cart(user=Depends(get_current_user),db:Session=Depends(get_db)):
    cart=db.query(Cart).filter(Cart.user_id==user.id).first()
    if cart: cart.items.clear(); db.commit()
