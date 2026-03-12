from contextlib import asynccontextmanager
from itertools import product
from fastapi import FastAPI,HTTPException
from sqlmodel import SQLModel,select,Session
from database import engine
from models import Product


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield
    print("Application stopped")


app = FastAPI(lifespan=lifespan)    

@app.post("/products/")
def add_product(product: Product):
    with Session(engine) as session:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

@app.get("/products/")
def get_products():
    with Session(engine) as session:
        # SQL: SELECT * FROM product;
        products = session.exec(select(Product)).all()
        return products



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


