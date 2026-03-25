from sqlmodel import Field,SQLModel 
from typing import Optional
from enum import Enum

class UnitType(str, Enum):
    kg = "kg"
    g = "g"
    l = "l"
    ml = "ml"
    szt = "szt"
    paczka = "paczka"


class ProductStatus(str, Enum):
    ACTIVE = "active"     
    PENDING = "pending"

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str 
    quantity: float
    unit: UnitType = Field(default=UnitType.szt)


    status: ProductStatus = Field(default=ProductStatus.ACTIVE)


