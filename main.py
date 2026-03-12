from contextlib import asynccontextmanager
from fastapi import FastAPI
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