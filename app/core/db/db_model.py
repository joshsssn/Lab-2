import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from dataclasses import dataclass, field, asdict


class ItemStatus(enum.Enum):
    AVAILABLE = "Available"
    SOLD = "Sold"
    REMOVED = "Removed"


@dataclass
class User:
    full_name: str
    username: str
    email: str
    password_hash: str
    rating: Decimal = Decimal("0.00")
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[int] = None
    _id: Optional[Any] = None  # MongoDB ObjectId

    def to_dict(self) -> dict:
        """Convert to MongoDB document format."""
        data = {
            "full_name": self.full_name,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "rating": float(self.rating),
            "created_at": self.created_at,
        }
        if self.id is not None:
            data["id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create User from MongoDB document."""
        return cls(
            id=data.get("id"),
            _id=data.get("_id"),
            full_name=data.get("full_name", ""),
            username=data.get("username", ""),
            email=data.get("email", ""),
            password_hash=data.get("password_hash", ""),
            rating=Decimal(str(data.get("rating", 0.0))),
            created_at=data.get("created_at", datetime.utcnow()),
        )


@dataclass
class Item:
    name: str
    price: Decimal
    owner_id: int
    description: Optional[str] = None
    status: ItemStatus = ItemStatus.AVAILABLE
    id: Optional[int] = None
    _id: Optional[Any] = None

    def to_dict(self) -> dict:
        """Convert to MongoDB document format."""
        data = {
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "status": self.status.value,
            "owner_id": self.owner_id,
        }
        if self.id is not None:
            data["id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        """Create Item from MongoDB document."""
        status_val = data.get("status", "Available")
        if isinstance(status_val, str):
            status = ItemStatus(status_val)
        else:
            status = status_val
        return cls(
            id=data.get("id"),
            _id=data.get("_id"),
            name=data.get("name", ""),
            description=data.get("description"),
            price=Decimal(str(data.get("price", 0.0))),
            status=status,
            owner_id=data.get("owner_id"),
        )


@dataclass
class Transaction:
    seller_id: int
    buyer_id: int
    item_id: int
    transaction_price: Decimal
    transaction_date: datetime = field(default_factory=datetime.utcnow)
    id: Optional[int] = None
    _id: Optional[Any] = None

    def to_dict(self) -> dict:
        """Convert to MongoDB document format."""
        data = {
            "seller_id": self.seller_id,
            "buyer_id": self.buyer_id,
            "item_id": self.item_id,
            "transaction_price": float(self.transaction_price),
            "transaction_date": self.transaction_date,
        }
        if self.id is not None:
            data["id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """Create Transaction from MongoDB document."""
        return cls(
            id=data.get("id"),
            _id=data.get("_id"),
            seller_id=data.get("seller_id"),
            buyer_id=data.get("buyer_id"),
            item_id=data.get("item_id"),
            transaction_price=Decimal(str(data.get("transaction_price", 0.0))),
            transaction_date=data.get("transaction_date", datetime.utcnow()),
        )


@dataclass
class Rating:
    transaction_id: int
    rater_id: int
    rated_id: int
    score: int
    id: Optional[int] = None
    _id: Optional[Any] = None

    def to_dict(self) -> dict:
        """Convert to MongoDB document format."""
        data = {
            "transaction_id": self.transaction_id,
            "rater_id": self.rater_id,
            "rated_id": self.rated_id,
            "score": self.score,
        }
        if self.id is not None:
            data["id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Rating":
        """Create Rating from MongoDB document."""
        return cls(
            id=data.get("id"),
            _id=data.get("_id"),
            transaction_id=data.get("transaction_id"),
            rater_id=data.get("rater_id"),
            rated_id=data.get("rated_id"),
            score=data.get("score", 0),
        )
