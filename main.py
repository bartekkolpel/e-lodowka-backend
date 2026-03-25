import os
import json
import io
from PIL import Image


from google import genai

from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, select, Session
from database import engine


from models import Product, ProductStatus


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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

@app.post("/scan-image/")
async def scan_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        prompt = f"""
        Przeanalizuj to zdjęcie (to może być paragon lub wnętrze lodówki).
        Znajdź wszystkie produkty spożywcze i zwróć je jako listę w formacie JSON.
        BARDZO WAŻNE: Skup się na dokładnej wadze lub objętości (np. 500g, 1L, 250ml, 0.75l).
        - Jeśli widzisz produkt z wagą (np. pomidory 500g), ustaw quantity: 500 i unit: "g".
        - Jeśli widzisz płyn (np. olej 1l), ustaw quantity: 1 i unit: "l". 
        - Używaj "szt" tylko wtedy, gdy nie ma podanej żadnej miary wagowej/objętościowej.
        - Dozwolone jednostki (unit) to WYŁĄCZNIE: "kg", "g", "l", "ml", "szt", "paczka".
        WAŻNE: Zwróć TYLKO czysty tekst JSON, bez formatowania Markdown (bez ```json na początku i końcu).
        Dozwolone jednostki (unit) to WYŁĄCZNIE: "kg", "g", "l", "ml", "szt", "paczka".
        Przykład:
        [
          {"name": "Mleko 2%", "quantity": 1, "unit": "szt"},
          {"name": "Jabłka", "quantity": 0.5, "unit": "kg"}
          {"name": "Pomidor", "quantity": 0,7, "unit": "kg"}
        ]
        """
        
        # NOWY SPOSÓB WYSYŁANIA ZDJĘCIA DO GEMINI:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=[prompt, image]
        )
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3]
        elif raw_text.startswith("```"):
             raw_text = raw_text[3:-3]
             
        products_data = json.loads(raw_text)
        
        with Session(engine) as session:
            for p_data in products_data:
                new_product = Product(
                    name=p_data["name"],
                    quantity=float(p_data["quantity"]),
                    unit=p_data["unit"],
                    status=ProductStatus.PENDING 
                )
                session.add(new_product)
            session.commit()
            
        return {"message": f"Sukces! AI znalazło {len(products_data)} produktów.", "products": products_data}

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"AI zwróciło zły format danych: {response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas skanowania: {str(e)}")


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
def update_product(product_id: int, new_quantity: float = None, new_unit: str = None, status: Optional[ProductStatus] = None):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Brak towaru!")
        if new_quantity is not None:
            product.quantity = new_quantity
        if new_unit is not None:
            product.unit = new_unit
        if status is not None:
            product.status = status

        session.add(product)
        session.commit()
        session.refresh(product)
        return product