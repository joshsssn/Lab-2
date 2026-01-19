from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum

class ItemStatus(str, Enum):
    AVAILABLE = "Available"
    SOLD = "Sold"
    REMOVED = "Removed"

class UserBase(BaseModel):
    full_name: str
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserResponse(UserBase):
    id: int
    rating: Decimal
    created_at: datetime

    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    status: ItemStatus = ItemStatus.AVAILABLE

class ItemCreate(ItemBase):
    owner_id: int

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    status: Optional[ItemStatus] = None

class ItemResponse(ItemBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class TransactionCreate(BaseModel):
    buyer_id: int
    item_id: int

class TransactionResponse(BaseModel):
    id: int
    seller_id: int
    buyer_id: int
    item_id: int
    transaction_price: Decimal
    transaction_date: datetime

    class Config:
        from_attributes = True

class RatingCreate(BaseModel):
    transaction_id: int
    score: int # Range 1-5 validation later

class RatingResponse(BaseModel):
    id: int
    transaction_id: int
    rater_id: int
    rated_id: int
    score: int

    class Config:
        from_attributes = True
