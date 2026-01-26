"""Test FastAPI serialization directly."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typing import List

# Import app components
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from app.core.config_manager import ConfigManager
from app.core.db.db_manager import DBManager
from app.core.db.db_model import User
from app.core.db.db_schema import UserResponse

# Create minimal test app
test_app = FastAPI()

configManager = ConfigManager()
dbManager = DBManager(configManager)

@test_app.get("/test_users", response_model=List[UserResponse])
def get_users():
    return dbManager.getRows(User)

# Test
client = TestClient(test_app)

try:
    response = client.get("/test_users")
    print("Status:", response.status_code)
    if response.status_code == 200:
        print("Success! First 500 chars:", response.text[:500])
    else:
        print("Error:", response.text)
except Exception as e:
    print("Exception:", e)
    import traceback
    traceback.print_exc()
