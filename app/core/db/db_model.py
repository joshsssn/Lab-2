import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL, Enum, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ItemStatus(enum.Enum):
    AVAILABLE = "Available"
    SOLD = "Sold"
    REMOVED = "Removed"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rating = Column(DECIMAL(3, 2), default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    items = relationship("Item", back_populates="owner")
    sales = relationship("Transaction", foreign_keys="Transaction.seller_id", back_populates="seller")
    purchases = relationship("Transaction", foreign_keys="Transaction.buyer_id", back_populates="buyer")


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Enum(ItemStatus), default=ItemStatus.AVAILABLE)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    owner = relationship("User", back_populates="items")
    transaction = relationship("Transaction", back_populates="item", uselist=False)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(Integer, ForeignKey("users.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    transaction_price = Column(DECIMAL(10, 2))
    transaction_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    seller = relationship("User", foreign_keys=[seller_id], back_populates="sales")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="purchases")
    item = relationship("Item", back_populates="transaction")
    rating = relationship("Rating", back_populates="transaction", uselist=False)


class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), unique=True)
    rater_id = Column(Integer, ForeignKey("users.id"))
    rated_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer, nullable=False)  # e.g., 1-5

    # Relationships
    transaction = relationship("Transaction", back_populates="rating")
    rater = relationship("User", foreign_keys=[rater_id])
    rated = relationship("User", foreign_keys=[rated_id])
