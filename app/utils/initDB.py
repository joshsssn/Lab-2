import pathlib
from sys import path

path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

from app.core.db.db_model import User, Item, Transaction, ItemStatus, Rating
from app.core.db.db_manager import DBManager
from app.core.config_manager import ConfigManager
from app.core.auth import get_password_hash
from decimal import Decimal


def dropAllCollections(dbManager: DBManager):
    """Drop all MongoDB collections."""
    dbManager.dropAllCollections()


def recreateIndexes(dbManager: DBManager):
    """Recreate indexes after dropping collections."""
    dbManager.users.create_index("username", unique=True)
    dbManager.users.create_index("email", unique=True)
    dbManager.users.create_index("id", unique=True)
    dbManager.items.create_index("id", unique=True)
    dbManager.transactions.create_index("id", unique=True)
    dbManager.ratings.create_index("id", unique=True)
    dbManager.ratings.create_index("transaction_id", unique=True)


import random

def populateUsers(dbManager: DBManager):
    """Populate MongoDB with sample users."""
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
    dbManager.insertRow(admin_user)
    dbManager.insertRow(test_user)
    
    users = []
    
    # Generate 300 users
    for i in range(300):
        username = f"user{i}"
        email = f"user{i}@example.com"
        password = "password"
        
        hashed_password = get_password_hash(password)
        
        user = User(
            full_name=f"User {i}",
            username=username,
            email=email,
            password_hash=hashed_password,
            rating=Decimal(random.uniform(1.0, 5.0)).quantize(Decimal("0.0"))
        )
        dbManager.insertRow(user)
        users.append(user)
    
    print(f"Populated {len(users) + 2} users.")
    return users


def populateItems(dbManager: DBManager):
    """Populate MongoDB with items from CSV."""
    # Get all users for random assignment
    users = dbManager.getRows(User)
    
    # Path to CSV
    csv_path = pathlib.Path(__file__).parent / "marketing_sample_for_ebay_com-ebay_com_product__20210101_20210331__30k_data.csv"
    print(f"DEBUG: Resolving CSV path to: {csv_path.resolve()}")
    
    try:
        if not csv_path.exists():
            print(f"ERROR: CSV file not found at {csv_path}")
            return []

        import pandas as pd
        try:
            df = pd.read_csv(csv_path, usecols=['Title', 'Price'], on_bad_lines='skip')
        except ValueError:
            df = pd.read_csv(csv_path, on_bad_lines='skip')

        print(f"DEBUG: Loaded CSV with {len(df)} rows.")
        
        # Filter for rows that have BOTH Title and Price
        df_clean = df.dropna(subset=['Title', 'Price'])
        print(f"DEBUG: {len(df_clean)} rows have valid Title and Price.")

        items = []
        # 95% Available, 5% Sold
        status_choices = [ItemStatus.AVAILABLE, ItemStatus.SOLD]
        status_weights = [0.95, 0.05]

        for index, row in df_clean.iterrows():
            # Clean Price: "$108.73" -> 108.73
            try:
                price_str = str(row['Price'])
                price_val = float(price_str.replace('$', '').replace(',', '').strip())
            except:
                continue
            
            title = str(row['Title'])
            desc = "Imported from eBay"
            
            # Weighted random choice
            status = random.choices(status_choices, weights=status_weights, k=1)[0]
            
            # Assign to random owner from our users
            if users:
                owner = random.choice(users)
                item = Item(
                    name=title[:100],
                    description=desc,
                    price=Decimal(price_val).quantize(Decimal("0.00")),
                    status=status,
                    owner_id=owner.id
                )
                dbManager.insertRow(item)
                items.append(item)
            
        print(f"Populated {len(items)} items from CSV.")
        return items
        
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []


def populateTransactionsAndRatings(dbManager: DBManager):
    """Create transactions for sold items and add ratings."""
    users = dbManager.getRows(User)
    # Find sold items
    all_items = dbManager.getRows(Item)
    sold_items = [item for item in all_items if item.status == ItemStatus.SOLD]
    
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
        dbManager.insertRow(tx)
        transactions.append(tx)
    
    print(f"Created {len(transactions)} transactions.")
    
    # Create ratings for ~80% of transactions
    ratings_count = 0
    for tx in transactions:
        if random.random() < 0.8:
            rating = Rating(
                transaction_id=tx.id,
                rater_id=tx.buyer_id,
                rated_id=tx.seller_id,
                score=random.randint(3, 5)
            )
            dbManager.insertRow(rating)
            ratings_count += 1
    
    print(f"Created {ratings_count} ratings.")
    
    # Update seller ratings based on new ratings
    for user in users:
        pipeline = [
            {"$match": {"rated_id": user.id}},
            {"$group": {"_id": None, "avg_score": {"$avg": "$score"}}}
        ]
        result = list(dbManager.ratings.aggregate(pipeline))
        if result:
            avg_score = result[0]["avg_score"]
            dbManager.users.update_one(
                {"id": user.id},
                {"$set": {"rating": round(avg_score, 1)}}
            )


def main():
    print("Initializing MongoDB database...")
    
    configManager = ConfigManager()
    dbManager = DBManager(configManager)

    print("Dropping all collections...")
    dropAllCollections(dbManager)
    
    print("Recreating indexes...")
    recreateIndexes(dbManager)

    print("Populating data...")
    populateUsers(dbManager)
    populateItems(dbManager)
    populateTransactionsAndRatings(dbManager)
    
    print("MongoDB database initialized successfully.")
    dbManager.close()


if __name__ == "__main__":
    main()
