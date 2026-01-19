import logging
import pathlib
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sys import path
from typing import List, Optional

path.append(str(pathlib.Path(__file__).resolve()))

from app.core.config_manager import ConfigManager
from app.core.log_manager import LogManager

from app.core.db.db_manager import DBManager
from app.core.db.db_model import User, Item
from app.core.db.db_schema import (
    UserCreate, UserUpdate, UserResponse, 
    ItemCreate, ItemUpdate, ItemResponse,
    TransactionCreate, TransactionResponse,
    Token, RatingCreate, RatingResponse
)
from app.core.auth import (
    get_password_hash, verify_password, 
    create_access_token, decode_access_token
)

logger = logging.getLogger(__name__)


confFilePath = pathlib.Path.cwd() / "app" / "conf" / "config.ini"

configManager = ConfigManager()

LogManager(configManager)
logger.info("Starting app")

logger.info(f"Config manager init successful with config file {confFilePath}")
logger.info("Logger manager init successful")


class Hello(BaseModel):
    message: str


app = FastAPI()

# CORS middleware to allow GUI requests
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    user = dbManager.getUserByUsername(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# This is for when we will need to store information the database
dbManager = DBManager(configManager)
logger.info("DB manager init succesful")


@app.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's profile information.
    """
    return current_user





@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticates a user and returns a JWT access token.
    Accepts standard OAuth2 password form (username/password).
    """
    user = dbManager.getUserByUsername(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users", response_model=UserResponse)
async def create_user(user_in: UserCreate):
    """
    Registers a new user in the system.
    Hashes the password before storage.
    """
    # Check if user already exists
    if dbManager.getUserByUsername(user_in.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    user = User(
        full_name=user_in.full_name,
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password)
    )
    if dbManager.insertRow(user):
        new_user = dbManager.getUserByUsername(user_in.username)
        if new_user:
            return new_user
    raise HTTPException(status_code=400, detail="User could not be created")


@app.get("/users", response_model=List[UserResponse])
async def get_all_users():
    """
    Retrieves a list of all users.
    """
    return dbManager.getRows(User)


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """
    Retrieves public profile information for a specific user.
    """
    user = dbManager.getUserById(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Updates a user's profile.
    Users can update their own profile, admin can update any user.
    """
    # Allow admin to update any user
    if user_id != current_user.id and current_user.username != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
        
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    updated_user = dbManager.updateUser(user_id, update_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found or update failed")
    return updated_user


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a user's profile.
    Users can delete their own profile, admin can delete any user.
    """
    # Allow admin to delete any user
    if user_id != current_user.id and current_user.username != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
        
    if dbManager.deleteUserById(user_id):
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/items", response_model=ItemResponse)
async def create_item(
    item_in: ItemCreate, 
    current_user: User = Depends(get_current_user)
):
    """
    Lists a new item for sale.
    The item is automatically assigned to the authenticated user.
    """
    from app.core.db.db_model import ItemStatus
    item = Item(
        name=item_in.name,
        description=item_in.description,
        price=item_in.price,
        status=ItemStatus(item_in.status.value),
        owner_id=current_user.id  # Use authenticated user ID
    )
    if dbManager.insertRow(item):
        # Find the item back to get ID (simple lookup by name and owner for this lab)
        all_items = dbManager.getRows(Item)
        for i in reversed(all_items):
            if i.name == item_in.name and i.owner_id == current_user.id:
                return i
    raise HTTPException(status_code=400, detail="Item could not be created")


@app.get("/items", response_model=List[ItemResponse])
async def get_available_items(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    keyword: Optional[str] = None,
    min_seller_rating: Optional[float] = None
):
    """
    Lists all available items with optional filtering.
    Filters: Price range, keyword in name/description, and minimum seller reputation.
    """
    return dbManager.getAvailableItems(
        min_price=min_price, 
        max_price=max_price, 
        keyword=keyword, 
        min_seller_rating=min_seller_rating
    )


@app.get("/items/seller/{seller_id}", response_model=List[ItemResponse])
async def get_items_by_seller(seller_id: int):
    """
    Retrieves all items (regardless of status) owned by a specific seller.
    """
    return dbManager.getItemsBySeller(seller_id)


@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int, 
    item_in: ItemUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Updates an existing item's details.
    Owner can update their items, admin can update any item.
    """
    # Check if item exists and belongs to user
    existing_item = dbManager.getRows(Item) # Need a better way but let's filter
    target_item = None
    for i in existing_item:
        if i.id == item_id:
            target_item = i
            break
    
    if not target_item:
        raise HTTPException(status_code=404, detail="Item not found")
    # Allow admin to update any item
    if target_item.owner_id != current_user.id and current_user.username != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to update this item")

    update_data = item_in.model_dump(exclude_unset=True)
    updated_item = dbManager.updateItem(item_id, update_data)
    if not updated_item:
        raise HTTPException(status_code=400, detail="Update failed")
    return updated_item


@app.post("/purchases", response_model=TransactionResponse)
async def purchase_item(
    transaction_in: TransactionCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Processes a purchase for an available item.
    - Prevents self-purchasing.
    - Updates item status to SOLD.
    - Creates a transaction record.
    """
    # Ensure the buyer is the current authenticated user
    if transaction_in.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Buyer ID must match authenticated user")

    transaction = dbManager.purchaseItem(
        buyer_id=current_user.id,
        item_id=transaction_in.item_id
    )
    if not transaction:
        raise HTTPException(
            status_code=400, 
            detail="Purchase failed. The item may not be available, or you are trying to buy your own item."
        )
    return transaction



@app.post("/ratings", response_model=RatingResponse)
async def rate_seller(
    rating_in: RatingCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Submit a rating for a seller after a successful transaction.
    - Validates that the rater is the buyer of the transaction.
    - Prevents duplicate ratings for the same transaction.
    - Automatically updates the seller's average rating.
    """
    if rating_in.score < 1 or rating_in.score > 5:
        raise HTTPException(status_code=400, detail="Score must be between 1 and 5")
    
    rating = dbManager.rateSeller(
        rater_id=current_user.id,
        transaction_id=rating_in.transaction_id,
        score=rating_in.score
    )
    if not rating:
        raise HTTPException(
            status_code=400, 
            detail="Rating failed. You may not be the buyer of this transaction, or it has already been rated."
        )
    return rating


@app.post("/api/predict-price")
async def predict_price_endpoint(payload: dict):
    title = payload.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    
    try:
        from price_predictor.inference import predict_price
        predicted_price = predict_price(title)
        return {"predicted_price": predicted_price}
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# Static files mount - MUST be at the end to not intercept API routes
# Reload trigger
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="gui", html=True), name="gui")
