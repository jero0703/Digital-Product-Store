from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base,engine
from .routers import auth,products,cart,orders,payments,admin

@asynccontextmanager
async def lifespan(app:FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app=FastAPI(title="Digital Product Store API",version="1.0.0",description="Backend-only REST API for a digital product store",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173"],allow_credentials=True,allow_methods=["GET","POST","PUT","DELETE","OPTIONS"],allow_headers=["Authorization","Content-Type"])
app.include_router(auth.router); app.include_router(products.router); app.include_router(cart.router); app.include_router(orders.router); app.include_router(payments.router); app.include_router(admin.router)
@app.get("/",tags=["System"])
def root(): return {"message":"Digital Product Store API","docs":"/docs"}
@app.get("/health",tags=["System"])
def health(): return {"status":"ok"}
