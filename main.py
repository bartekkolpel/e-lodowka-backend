from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel,select,Session
from database import engine
from models import Product
from models import Product, ProductStatus

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield
    print("Application stopped")


app = FastAPI(lifespan=lifespan)    


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)


@app.post("/products/")
def add_product(product: Product):
    with Session(engine) as session:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

@app.get("/products/")
def get_products(status: ProductStatus = ProductStatus.ACTIVE):
    with Session(engine) as session:
        products = session.exec(select(Product).where(Product.status == status)).all()
        return products


@app.post("/products/bulk")
def add_multiple_products(products: List[Product]):
    with Session(engine) as session:
        for p in products:
            p.status = ProductStatus.PENDING 
            session.add(p)
        session.commit()
        return {"message": f"Pomyślnie wrzucono {len(products)} produktów do poczekalni!"}



@app.delete("/products/{product_id}")
def delete_product(product_id: int): 
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Brak towaru w lodówce!")
        session.delete(product)
        session.commit()
        
        print(f"LOG: Usunięto produkt o ID {product_id}") 
        return {"ok": True, "message": f"Produkt {product.name} usunięty."}    



@app.patch("/products/{product_id}")
def update_product(product_id: int, new_quantity: float = None, new_unit: str = None):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Brak towaru!")
        if new_quantity is not None:
            product.quantity = new_quantity
        if new_unit is not None:
            product.unit = new_unit

        session.add(product)
        session.commit()
        session.refresh(product)
        return product


