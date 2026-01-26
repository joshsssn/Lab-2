import logging
from typing import List, Any, Optional, Type, Dict
from decimal import Decimal

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from app.core.config_manager import ConfigManager
from app.core.db.db_model import User, Item, Transaction, Rating, ItemStatus

logger = logging.getLogger(__name__)


class DBManager:
    """
    MongoDB-based database manager for semi-structured document storage.
    Replaces the previous SQLAlchemy-based implementation.
    """

    def __init__(self, configManager: ConfigManager):
        self.dbType = configManager.getDBType()
        self.dbUrl = configManager.getDBUrl()
        self.dbName = configManager.getMongoDBName()
        self.client: MongoClient = MongoClient(self.dbUrl)
        self.db: Database = self.client[self.dbName]
        
        # Collections
        self.users: Collection = self.db["users"]
        self.items: Collection = self.db["items"]
        self.transactions: Collection = self.db["transactions"]
        self.ratings: Collection = self.db["ratings"]
        self.counters: Collection = self.db["counters"]
        
        # Ensure indexes for unique fields
        self.users.create_index("username", unique=True)
        self.users.create_index("email", unique=True)
        self.users.create_index("id", unique=True)
        self.items.create_index("id", unique=True)
        self.transactions.create_index("id", unique=True)
        self.ratings.create_index("id", unique=True)
        self.ratings.create_index("transaction_id", unique=True)
        
        logger.info(f"Connected to MongoDB at {self.dbUrl}")

    def _getNextId(self, collection_name: str) -> int:
        """Auto-increment ID generator for MongoDB documents."""
        result = self.counters.find_one_and_update(
            {"_id": collection_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        return result["seq"]

    def insertRow(self, row: Any) -> bool:
        """
        Inserts a new document into the appropriate collection.
        :param row: The model instance to add (User, Item, Transaction, or Rating).
        :return: Boolean indicating success.
        """
        try:
            if isinstance(row, User):
                row.id = self._getNextId("users")
                self.users.insert_one(row.to_dict())
            elif isinstance(row, Item):
                row.id = self._getNextId("items")
                self.items.insert_one(row.to_dict())
            elif isinstance(row, Transaction):
                row.id = self._getNextId("transactions")
                self.transactions.insert_one(row.to_dict())
            elif isinstance(row, Rating):
                row.id = self._getNextId("ratings")
                self.ratings.insert_one(row.to_dict())
            else:
                logger.warning(f"Unknown row type: {type(row)}")
                return False
            return True
        except Exception as e:
            logger.warning(f"Unable to insert row with exception {e}")
            return False

    def removeRow(self, row: Any) -> bool:
        """
        Remove a document from its collection.
        :param row: The model instance to delete.
        :return: Boolean indicating success.
        """
        try:
            if isinstance(row, User):
                self.users.delete_one({"id": row.id})
            elif isinstance(row, Item):
                self.items.delete_one({"id": row.id})
            elif isinstance(row, Transaction):
                self.transactions.delete_one({"id": row.id})
            elif isinstance(row, Rating):
                self.ratings.delete_one({"id": row.id})
            else:
                return False
            return True
        except Exception as e:
            logger.warning(f"Unable to remove row with exception {e}")
            return False

    def getRows(self, objType: Type) -> List[Any]:
        """Get all documents from a collection."""
        try:
            if objType == User:
                return [User.from_dict(doc) for doc in self.users.find()]
            elif objType == Item:
                return [Item.from_dict(doc) for doc in self.items.find()]
            elif objType == Transaction:
                return [Transaction.from_dict(doc) for doc in self.transactions.find()]
            elif objType == Rating:
                return [Rating.from_dict(doc) for doc in self.ratings.find()]
            return []
        except Exception as e:
            logger.warning(f"Unable to get rows: {e}")
            return []

    def getUserById(self, user_id: int) -> Optional[User]:
        """Find a user by their ID."""
        doc = self.users.find_one({"id": user_id})
        return User.from_dict(doc) if doc else None

    def getUserByUsername(self, username: str) -> Optional[User]:
        """Find a user by their username."""
        doc = self.users.find_one({"username": username})
        return User.from_dict(doc) if doc else None

    def deleteUserById(self, user_id: int) -> bool:
        """Delete a user by their ID."""
        try:
            result = self.users.delete_one({"id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.warning(f"Unable to delete user {user_id}: {e}")
            return False

    def updateUser(self, user_id: int, update_data: dict) -> Optional[User]:
        """Update a user's attributes."""
        try:
            # Convert Decimal to float for MongoDB
            for key, value in update_data.items():
                if isinstance(value, Decimal):
                    update_data[key] = float(value)
            
            result = self.users.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            if result.modified_count > 0 or result.matched_count > 0:
                return self.getUserById(user_id)
            return None
        except Exception as e:
            logger.warning(f"Unable to update user {user_id}: {e}")
            return None

    def getAvailableItems(
        self, 
        min_price: Optional[float] = None, 
        max_price: Optional[float] = None, 
        keyword: Optional[str] = None,
        min_seller_rating: Optional[float] = None
    ) -> List[Item]:
        """
        Retrieves items with status 'AVAILABLE', optionally filtered.
        """
        try:
            query: Dict[str, Any] = {"status": ItemStatus.AVAILABLE.value}
            
            if min_price is not None:
                query["price"] = query.get("price", {})
                query["price"]["$gte"] = min_price
            if max_price is not None:
                query["price"] = query.get("price", {})
                query["price"]["$lte"] = max_price
            if keyword:
                query["$or"] = [
                    {"name": {"$regex": keyword, "$options": "i"}},
                    {"description": {"$regex": keyword, "$options": "i"}}
                ]
            
            items = [Item.from_dict(doc) for doc in self.items.find(query)]
            
            # Filter by seller rating if needed
            if min_seller_rating is not None:
                filtered_items = []
                for item in items:
                    seller = self.getUserById(item.owner_id)
                    if seller and float(seller.rating) >= min_seller_rating:
                        filtered_items.append(item)
                return filtered_items
            
            return items
        except Exception as e:
            logger.warning(f"Error getting available items: {e}")
            return []

    def getItemsBySeller(self, seller_id: int) -> List[Item]:
        """Retrieves all items belonging to a specific user."""
        try:
            return [Item.from_dict(doc) for doc in self.items.find({"owner_id": seller_id})]
        except Exception as e:
            logger.warning(f"Error getting items by seller: {e}")
            return []

    def updateItem(self, item_id: int, update_data: dict) -> Optional[Item]:
        """Updates an item's attributes."""
        try:
            # Handle status enum conversion
            if "status" in update_data:
                status_val = update_data["status"]
                if hasattr(status_val, 'value'):
                    update_data["status"] = status_val.value
                elif isinstance(status_val, str):
                    # Validate it's a valid status
                    try:
                        ItemStatus(status_val)
                    except ValueError:
                        del update_data["status"]
            
            # Convert Decimal to float
            for key, value in update_data.items():
                if isinstance(value, Decimal):
                    update_data[key] = float(value)
            
            result = self.items.update_one(
                {"id": item_id},
                {"$set": update_data}
            )
            if result.modified_count > 0 or result.matched_count > 0:
                doc = self.items.find_one({"id": item_id})
                return Item.from_dict(doc) if doc else None
            return None
        except Exception as e:
            logger.warning(f"Unable to update item {item_id}: {e}")
            return None

    def purchaseItem(self, buyer_id: int, item_id: int) -> Optional[Transaction]:
        """
        Handles the purchase of an item.
        - Validates item availability.
        - Checks that the buyer is not the seller.
        - Updates item status to 'SOLD'.
        - Creates and returns a Transaction record.
        """
        try:
            # 1. Fetch item
            item_doc = self.items.find_one({"id": item_id})
            if not item_doc:
                logger.warning(f"Item {item_id} not found")
                return None
            
            item = Item.from_dict(item_doc)
            
            # 2. Check if item is available
            if item.status != ItemStatus.AVAILABLE:
                logger.warning(f"Item {item_id} is not available (Status: {item.status})")
                return None
            
            # 3. Prevent self-purchase
            if item.owner_id == buyer_id:
                logger.warning(f"Buyer {buyer_id} cannot purchase their own item {item_id}")
                return None

            # 4. Create Transaction
            transaction = Transaction(
                seller_id=item.owner_id,
                buyer_id=buyer_id,
                item_id=item_id,
                transaction_price=item.price
            )
            transaction.id = self._getNextId("transactions")
            self.transactions.insert_one(transaction.to_dict())
            
            # 5. Update Item Status
            self.items.update_one(
                {"id": item_id},
                {"$set": {"status": ItemStatus.SOLD.value}}
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Purchase failed for item {item_id} by buyer {buyer_id}: {e}")
            return None

    def rateSeller(self, rater_id: int, transaction_id: int, score: int) -> Optional[Rating]:
        """
        Submits a rating for a transaction.
        - Verification: Rater must be the buyer.
        - Verification: Transaction must not have been rated yet.
        - Side Effect: Recalculates and updates the seller's average rating.
        """
        try:
            # 1. Verify transaction
            tx_doc = self.transactions.find_one({"id": transaction_id})
            if not tx_doc:
                logger.warning(f"Transaction {transaction_id} not found")
                return None
            
            tx = Transaction.from_dict(tx_doc)
            
            # 2. Verify rater is buyer
            if tx.buyer_id != rater_id:
                logger.warning(f"User {rater_id} is not the buyer of transaction {transaction_id}")
                return None
            
            # 3. Check if already rated
            existing = self.ratings.find_one({"transaction_id": transaction_id})
            if existing:
                logger.warning(f"Transaction {transaction_id} already rated")
                return None
            
            # 4. Create rating
            rating = Rating(
                transaction_id=transaction_id,
                rater_id=rater_id,
                rated_id=tx.seller_id,
                score=score
            )
            rating.id = self._getNextId("ratings")
            self.ratings.insert_one(rating.to_dict())

            # 5. Update seller average rating
            pipeline = [
                {"$match": {"rated_id": tx.seller_id}},
                {"$group": {"_id": None, "avg_score": {"$avg": "$score"}}}
            ]
            result = list(self.ratings.aggregate(pipeline))
            if result:
                avg_score = result[0]["avg_score"]
                self.users.update_one(
                    {"id": tx.seller_id},
                    {"$set": {"rating": round(avg_score, 2)}}
                )
            
            return rating
        except Exception as e:
            logger.error(f"Rating failed: {e}")
            return None

    def dropAllCollections(self):
        """Drop all collections - used for database reset."""
        self.users.drop()
        self.items.drop()
        self.transactions.drop()
        self.ratings.drop()
        self.counters.drop()
        logger.info("All collections dropped")

    def close(self):
        """Close the MongoDB connection."""
        self.client.close()
