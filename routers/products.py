from fastapi import APIRouter,Depends,HTTPException,Query,status
from sqlalchemy import or_,func
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_admin
from app.models import Product
from app.schemas import ProductCreate,ProductUpdate,ProductResponse,ProductPage
from app.utils.pagination import page_meta
router=APIRouter(prefix="/products",tags=["Products"])

@router.post("",response_model=ProductResponse,status_code=201)
def create_product(data:ProductCreate,db:Session=Depends(get_db),_=Depends(get_current_admin)):
    p=Product(**data.model_dump()); db.add(p); db.commit(); db.refresh(p); return p

@router.get("",response_model=ProductPage)
def list_products(page:int=Query(1,ge=1),limit:int=Query(10,ge=1,le=100),search:str|None=None,db:Session=Depends(get_db)):
    q=db.query(Product).filter(Product.is_active==True)
    if search and search.strip():
        term=f"%{search.strip()}%"; q=q.filter(or_(Product.name.ilike(term),Product.description.ilike(term),Product.category.ilike(term)))
    total=q.with_entities(func.count(Product.id)).scalar() or 0
    items=q.order_by(Product.id.desc()).offset((page-1)*limit).limit(limit).all()
    return {"items":items,**page_meta(total,page,limit)}

@router.get("/{product_id}",response_model=ProductResponse)
def get_product(product_id:int,db:Session=Depends(get_db)):
    p=db.query(Product).filter(Product.id==product_id,Product.is_active==True).first()
    if not p: raise HTTPException(404,"Product not found")
    return p

@router.put("/{product_id}",response_model=ProductResponse)
def update_product(product_id:int,data:ProductUpdate,db:Session=Depends(get_db),_=Depends(get_current_admin)):
    p=db.query(Product).filter(Product.id==product_id).first()
    if not p: raise HTTPException(404,"Product not found")
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(p,k,v.strip() if isinstance(v,str) else v)
    db.commit(); db.refresh(p); return p

@router.delete("/{product_id}",status_code=204)
def delete_product(product_id:int,db:Session=Depends(get_db),_=Depends(get_current_admin)):
    p=db.query(Product).filter(Product.id==product_id).first()
    if not p: raise HTTPException(404,"Product not found")
    p.is_active=False; db.commit()
