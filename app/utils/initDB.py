import pathlib
from sys import path

path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

from app.core.db.db_model import Base, User, Item, Transaction, ItemStatus, Rating
from app.core.db.db_manager import DBManager
from app.core.config_manager import ConfigManager
from app.core.auth import get_password_hash
from decimal import Decimal


def createTables(engine):
    Base.metadata.create_all(engine)


def dropAllTables(engine):
    Base.metadata.drop_all(engine)


import random

def populateUsers(session):
    first_names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Hank", "Ivy", "Jack", 
                   "Liam", "Mia", "Noah", "Olivia", "Peter", "Quinn", "Rose", "Sam", "Tara", "Ursula"]
    last_names = ["Smith", "Jones", "Brown", "Wilson", "Miller", "Thomas", "Lee", "Green", "White", "Black", 
                  "Taylor", "Anderson", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Lewis"]
    
    users = []
    pw_hash = get_password_hash("password123")
    usernames = set()
    
    # Generate 50 unique users
    for i in range(50):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        username = f"{fn.lower()}_{ln.lower()}_{i}"
        email = f"{username}@example.com"
        
        users.append(User(
            full_name=f"{fn} {ln}",
            username=username,
            email=email,
            password_hash=pw_hash,
            rating=Decimal(random.uniform(3.0, 5.0)).quantize(Decimal("0.0"))
        ))
    
    session.add_all(users)
    session.commit()


def populateItems(session):
    users = session.query(User).all()
    
    adjectives = ["Vintage", "Modern", "Sleek", "Sturdy", "Reliable", "Classic", "Premium", "Budget", "Rare", "Essential"]
    nouns = ["Camera", "Bike", "Laptop", "Smartphone", "Watch", "Guitar", "Headphones", "Speaker", "Monitor", "Keyboard",
             "Desk", "Chair", "Lamp", "Backpack", "Tool", "Book", "Console", "Tablet", "Microwave", "Blender"]
    
    items = []
    status_options = [ItemStatus.AVAILABLE, ItemStatus.AVAILABLE, ItemStatus.AVAILABLE, ItemStatus.SOLD, ItemStatus.REMOVED]

    # Generate 200 items
    for i in range(200):
        adj = random.choice(adjectives)
        noun = random.choice(nouns)
        name = f"{adj} {noun}"
        price = Decimal(random.uniform(10.0, 1500.0)).quantize(Decimal("0.00"))
        status = random.choice(status_options)
        owner = random.choice(users)
        
        items.append(Item(
            name=name,
            description=f"A high-quality {name.lower()} in excellent condition. Perfect for daily use.",
            price=price,
            status=status,
            owner_id=owner.id
        ))
    
    session.add_all(items)
    session.commit()


def populateTransactionsAndRatings(session):
    users = session.query(User).all()
    # Find sold items to create transactions for them
    sold_items = session.query(Item).filter(Item.status == ItemStatus.SOLD).all()
    
    transactions = []
    for item in sold_items:
        buyer = random.choice(users)
        while buyer.id == item.owner_id:
            buyer = random.choice(users)
            
        tx = Transaction(
            seller_id=item.owner_id,
            buyer_id=buyer.id,
            item_id=item.id,
            transaction_price=item.price
        )
        transactions.append(tx)
    
    session.add_all(transactions)
    session.flush() # Get IDs for ratings
    
    ratings = []
    for tx in transactions:
        # Rate about 80% of transactions
        if random.random() < 0.8:
            ratings.append(Rating(
                transaction_id=tx.id,
                rater_id=tx.buyer_id,
                rated_id=tx.seller_id,
                score=random.randint(3, 5)
            ))
            
    session.add_all(ratings)
    session.commit()
    
    # Update seller ratings based on new ratings
    from sqlalchemy import func
    for user in users:
        avg_score = session.query(func.avg(Rating.score)).filter(Rating.rated_id == user.id).scalar()
        if avg_score:
            user.rating = Decimal(avg_score).quantize(Decimal("0.0"))
    
    session.commit()


def populateTransactions(session):
    # Fetch data to link them
    users = session.query(User).all()
    items = session.query(Item).all()
    
    alice = users[0]
    bob = users[1]
    charlie = users[2]
    laptop = items[2] # Laptop was sold by Alice

    t1 = Transaction(
        seller_id=alice.id,
        buyer_id=charlie.id,
        item_id=laptop.id,
        transaction_price=Decimal("1100.00")
    )
    session.add(t1)
    session.commit()


def main():

    configManager = ConfigManager()
    dbManager = DBManager(configManager)
    engine = dbManager.getEngine()

    logger = dbManager.session.get_bind().logger if hasattr(dbManager.session.get_bind(), "logger") else None

    print("Dropping tables...")
    dropAllTables(engine)
    print("Creating tables...")
    createTables(engine)

    print("Populating data...")
    populateUsers(dbManager.session)
    populateItems(dbManager.session)
    populateTransactionsAndRatings(dbManager.session)
    print("Database initialized successfully.")


if __name__ == "__main__":
    main()
