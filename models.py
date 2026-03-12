from sqlmodel import Field,SQLModel 
from typing import Optional




class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str 
    quantity: float
    unit: str



