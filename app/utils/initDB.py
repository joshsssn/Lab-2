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
    # Add default accounts first
    admin_user = User(
        full_name="Admin User",
        username="admin",
        email="admin@marketplace.com",
        password_hash=get_password_hash("admin"),
        rating=Decimal("5.0")
    )
    test_user = User(
        full_name="Test User",
        username="test",
        email="test@marketplace.com",
        password_hash=get_password_hash("test"),
        rating=Decimal("4.0")
    )
    session.add_all([admin_user, test_user])
    session.commit()
    
    first_names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Hank", "Ivy", "Jack", 
                   "Liam", "Mia", "Noah", "Olivia", "Peter", "Quinn", "Rose", "Sam", "Tara", "Ursula"]
    last_names = ["Smith", "Jones", "Brown", "Wilson", "Miller", "Thomas", "Lee", "Green", "White", "Black", 
                  "Taylor", "Anderson", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Lewis"]
    
    users = []
    pw_hash = get_password_hash("password123")
    
    # Generate 300 users
    for i in range(300):
        username = f"user{i}"
        email = f"user{i}@example.com"
        password = "password"
        
        hashed_password = get_password_hash(password)
        
        users.append(User(
            full_name=f"User {i}", # Added full_name for consistency
            username=username,
            email=email,
            password_hash=hashed_password,
            rating=Decimal(random.uniform(1.0, 5.0)).quantize(Decimal("0.0")) # Changed to Decimal and quantize
        ))
    
    session.add_all(users)
    session.commit()
    print(f"Populated {len(users)} users.")


def populateItems(session):
    users = session.query(User).all()
    
    # Path to CSV
    csv_path = pathlib.Path(__file__).parent / "marketing_sample_for_ebay_com-ebay_com_product__20210101_20210331__30k_data.csv"
    print(f"DEBUG: Resolving CSV path to: {csv_path.resolve()}")
    
    try:
        if not csv_path.exists():
            print(f"ERROR: CSV file not found at {csv_path}")
            return

        import pandas as pd
        # on_bad_lines='skip' ensures we don't crash on malformed rows
        # User requested to be less aggressive with skipping. We only need Title and Price.
        # Reading only specific columns helps avoid tokenizing errors in irrelevant columns like Description
        try:
            df = pd.read_csv(csv_path, usecols=['Title', 'Price'], on_bad_lines='skip')
        except ValueError:
            # Fallback if columns are named differently (though we saw them in header)
            df = pd.read_csv(csv_path, on_bad_lines='skip')

        print(f"DEBUG: Loaded CSV with {len(df)} rows.")
        
        # Filter for rows that have BOTH Title and Price
        df_clean = df.dropna(subset=['Title', 'Price'])
        print(f"DEBUG: {len(df_clean)} rows have valid Title and Price.")

        items = []
        # 95% Available, 5% Sold/Removed (Sold is usually better for testing than Removed)
        status_choices = [ItemStatus.AVAILABLE, ItemStatus.SOLD]
        status_weights = [0.95, 0.05]

        for index, row in df_clean.iterrows():
            # Clean Price: "$108.73" -> 108.73
            try:
                price_str = str(row['Price'])
                # Remove currency symbols and cleanup
                price_val = float(price_str.replace('$', '').replace(',', '').strip())
            except:
                continue # Skip if price is unparseable despite notna check
            
            title = str(row['Title'])
            # Description is "Imported from eBay" as requested "le reste on s'en fiche"
            desc = "Imported from eBay" 
            
            # Weighted random choice
            status = random.choices(status_choices, weights=status_weights, k=1)[0]
            
            # Assign to random owner from our 300 users
            if users:
                owner = random.choice(users)
                items.append(Item(
                    name=title[:100], 
                    description=desc,
                    price=Decimal(price_val).quantize(Decimal("0.00")),
                    status=status,
                    owner_id=owner.id
                ))
            
        session.add_all(items)
        session.commit()
        print(f"Populated {len(items)} items from CSV.")
        
    except Exception as e:
        print(f"Error loading CSV: {e}")



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
