"""Simple test script to debug serialization issues."""
from app.core.db.db_manager import DBManager
from app.core.config_manager import ConfigManager
from app.core.db.db_model import User
from app.core.db.db_schema import UserResponse
import json

cm = ConfigManager()
dm = DBManager(cm)

# Get first user
users = dm.getRows(User)
u = users[0]

print("_id type:", type(u._id))
print("User object:", u)

# Try to convert to dict and JSON
try:
    # Create UserResponse using from_attributes
    ur = UserResponse.model_validate(u)
    print("UserResponse created:", ur)
    
    # Try JSON serialization
    json_str = ur.model_dump_json()
    print("JSON output:", json_str[:300])
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
