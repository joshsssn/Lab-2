import logging
from typing import List, Any, Optional, Type, Dict, Tuple

import pandas as pd
from pandas import DataFrame
from sqlalchemy import create_engine, and_, text, desc, or_
from sqlalchemy.orm import sessionmaker
from app.core.config_manager import ConfigManager
from app.core.db.db_model import User, Item, Transaction

logger = logging.getLogger(__name__)


class DBManager:

    def __init__(self, configManager: ConfigManager):
        self.dbType = configManager.getDBType()
        self.dbUrl = configManager.getDBUrl()
        self.engine = self._buildEngine()
        self.session = self.getSession()

    def _buildEngine(
        self,
    ):
        if self.dbType == "sqlite":
            # 'sqlite:///C:\\path\\to\\foo.db'
            return create_engine(f"sqlite:///{self.dbUrl}", echo=True)
        elif self.dbType == "mysql":
            # 'mysql+pymysql://scott:tiger@localhost:3306/foo'
            return create_engine(f"mysql+pymysql://{self.dbUrl}", echo=True)
        elif self.dbType == "postgresql":
            # 'postgresql+psycopg2://scott:tiger@localhost:5432/foo'
            return create_engine(f"postgresql+psycopg2://{self.dbUrl}", echo=True)
        else:
            raise NotImplementedError

    def getEngine(self):
        return self.engine

    def getSession(self):
        Session = sessionmaker(bind=self.engine)
        return Session()

    def insertRow(self, row):
        """
        Inserts a new row into the database.
        :param row: The model instance to add.
        :return: Boolean indicating success.
        """
        result = False
        session = self.getSession()
        try:
            session.add(row)
            session.commit()
            result = True
        except Exception as e:
            logger.warning(f"Unable to insert row with exception {e}")
        finally:
            session.close()
            return result

    def removeRow(self, row):
        """
        Remove a row in a table.
        :param row: The model instance to delete.
        :return: Boolean indicating success.
        """
        result = False
        session = self.getSession()
        try:
            session.delete(row)
            session.commit()
            result = True
        except Exception as e:
            logger.warning(f"Unable to remove row with exception {e}")
        finally:
            session.close()
            return result

    def executeRawSqlQuery(self, sqlQuery: str) -> DataFrame:
        """
        This function takes a raw sql text, then run it in a sqlalchemy engine. At last, it converts the result
        into a pandas dataframe
        :param sqlQuery:
        :return:
        """
        conn = self.engine.connect()
        query = conn.execute(text(sqlQuery))
        df = pd.DataFrame(query.fetchall())
        conn.close()
        return df

    def getRows(self, objName) -> Any:
        session = self.getSession()
        rows = session.query(objName).all()
        session.close()
        return rows

    def getUserById(self, user_id: int) -> Optional[User]:
        session = self.getSession()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def getUserByUsername(self, username: str) -> Optional[User]:
        session = self.getSession()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            session.close()

    def deleteUserById(self, user_id: int) -> bool:
        session = self.getSession()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                session.delete(user)
                session.commit()
                return True
            return False
        except Exception as e:
            logger.warning(f"Unable to delete user {user_id}: {e}")
            return False
        finally:
            session.close()

    def updateUser(self, user_id: int, update_data: dict) -> Optional[User]:
        session = self.getSession()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                for key, value in update_data.items():
                    if value is not None:
                        setattr(user, key, value)
                session.commit()
                # Refresh from DB before closing session
                session.refresh(user)
                return user
            return None
        except Exception as e:
            logger.warning(f"Unable to update user {user_id}: {e}")
            return None
        finally:
            session.close()

    def getAvailableItems(
        self, 
        min_price: Optional[float] = None, 
        max_price: Optional[float] = None, 
        keyword: Optional[str] = None,
        min_seller_rating: Optional[float] = None
    ) -> List[Item]:
        """
        Retrieves items with status 'AVAILABLE', optionally filtered by price, keyword, and seller rating.
        :param min_price: Minimum price filter.
        :param max_price: Maximum price filter.
        :param keyword: Search in item name and description.
        :param min_seller_rating: Minimum average rating of the seller.
        :return: List of Item objects.
        """
        session = self.getSession()
        try:
            from app.core.db.db_model import ItemStatus, User
            query = session.query(Item).join(User, Item.owner_id == User.id)
            query = query.filter(Item.status == ItemStatus.AVAILABLE)
            
            if min_price is not None:
                query = query.filter(Item.price >= min_price)
            if max_price is not None:
                query = query.filter(Item.price <= max_price)
            if keyword:
                query = query.filter(
                    or_(
                        Item.name.ilike(f"%{keyword}%"),
                        Item.description.ilike(f"%{keyword}%")
                    )
                )
            if min_seller_rating is not None:
                query = query.filter(User.rating >= min_seller_rating)
                
            return query.all()
        finally:
            session.close()

    def getItemsBySeller(self, seller_id: int) -> List[Item]:
        """
        Retrieves all items belonging to a specific user.
        """
        session = self.getSession()
        try:
            return session.query(Item).filter(Item.owner_id == seller_id).all()
        finally:
            session.close()

    def updateItem(self, item_id: int, update_data: dict) -> Optional[Item]:
        """
        Updates an item's attributes based on the provided dictionary.
        """
        session = self.getSession()
        try:
            item = session.query(Item).filter(Item.id == item_id).first()
            if item:
                for key, value in update_data.items():
                    if value is not None:
                        # Handle Enum conversion if status is passed as string
                        if key == "status" and isinstance(value, str):
                            from app.core.db.db_model import ItemStatus
                            try:
                                value = ItemStatus(value)
                            except ValueError:
                                continue
                        setattr(item, key, value)
                session.commit()
                session.refresh(item)
                return item
            return None
        except Exception as e:
            logger.warning(f"Unable to update item {item_id}: {e}")
            return None
        finally:
            session.close()

    def purchaseItem(self, buyer_id: int, item_id: int) -> Optional[Transaction]:
        """
        Handles the purchase of an item.
        - Validates item availability.
        - Checks that the buyer is not the seller.
        - Updates item status to 'SOLD'.
        - Creates and returns a Transaction record.
        """
        session = self.getSession()
        try:
            from app.core.db.db_model import ItemStatus
            
            # 1. Fetch item
            item = session.query(Item).filter(Item.id == item_id).first()
            if not item:
                logger.warning(f"Item {item_id} not found")
                return None
            
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
            
            # 5. Update Item Status
            item.status = ItemStatus.SOLD
            
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            return transaction
            
        except Exception as e:
            logger.error(f"Purchase failed for item {item_id} by buyer {buyer_id}: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def rateSeller(self, rater_id: int, transaction_id: int, score: int) -> Optional[Any]:
        """
        Submits a rating for a transaction.
        - Verification: Rater must be the buyer.
        - Verification: Transaction must not have been rated yet.
        - Side Effect: Recalculates and updates the seller's average rating.
        """
        session = self.getSession()
        try:
            from app.core.db.db_model import Rating, User, Transaction
            from sqlalchemy import func

            # 1. Verify transaction
            tx = session.query(Transaction).filter(Transaction.id == transaction_id).first()
            if not tx:
                logger.warning(f"Transaction {transaction_id} not found")
                return None
            
            # 2. Verify rater is buyer
            if tx.buyer_id != rater_id:
                logger.warning(f"User {rater_id} is not the buyer of transaction {transaction_id}")
                return None
            
            # 3. Check if already rated
            existing = session.query(Rating).filter(Rating.transaction_id == transaction_id).first()
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
            session.add(rating)
            session.flush() # flush to include in calc

            # 5. Update seller average rating
            seller = session.query(User).filter(User.id == tx.seller_id).first()
            avg_score = session.query(func.avg(Rating.score)).filter(Rating.rated_id == tx.seller_id).scalar()
            seller.rating = avg_score
            
            session.commit()
            session.refresh(rating)
            return rating
        except Exception as e:
            logger.error(f"Rating failed: {e}")
            session.rollback()
            return None
        finally:
            session.close()
