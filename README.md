# NotEbay - Marketplace API with GUI

A comprehensive marketplace application built with FastAPI backend and a modern web-based GUI. This project implements a secure, scalable e-commerce platform inspired by eBay.

## Features

### Backend API
- **User Authentication**: Secure registration and login using PBKDF2 password hashing and JWT tokens
- **User Management**: Full CRUD operations for user profiles
- **Item Listings**: Create, update, and browse marketplace items with filtering
- **Transaction System**: Purchase flow with item status tracking (`AVAILABLE`, `SOLD`, `REMOVED`)
- **Rating System**: Buyers can rate sellers, with automatic average rating calculations
- **Advanced Filtering**: Search items by keywords, price range, and seller reputation

### Web GUI (`gui/`)
- **Modern Dark Theme**: eBay-inspired color scheme (red, blue, yellow, green)
- **Authentication**: Login and registration forms with validation
- **Browse Items**: Grid view with search and filter capabilities
- **Browse Users**: View all sellers and their item listings
- **Purchase Flow**: Buy items with instant feedback
- **Rating System**: Star-based rating after purchase
- **Seller Profiles**: Click seller name to view their profile and items

## Architecture

```
├── main.py                 # FastAPI application with all endpoints
├── gui/                    # Web-based GUI
│   ├── index.html          # Main HTML structure
│   ├── styles.css          # eBay-themed styling
│   └── app.js              # API client and UI logic
├── app/
│   ├── core/
│   │   ├── auth.py         # JWT token and password hashing
│   │   ├── config_manager.py
│   │   ├── log_manager.py
│   │   └── db/
│   │       ├── db_manager.py   # Database operations
│   │       ├── db_model.py     # SQLAlchemy models
│   │       └── db_schema.py    # Pydantic schemas
│   └── utils/
│       └── initDB.py       # Database seeding script
└── requirements.txt
```

## Installation

1. **Environment Setup**:
   ```bash
   uv sync
   ```

2. **Configuration**:
   - Copy `app/conf/config_template.ini` to `app/conf/config.ini`
   - Configure your settings as needed

3. **Initialize Database**:
   ```bash
   uv run app/utils/initDB.py
   ```
   This creates 52 users (including `admin`/`admin` and `test`/`test`) and 200 items.

## Usage

### Start the API Server
```bash
uv run fastapi dev
```

### Access the Application
- **GUI**: Open `gui/index.html` in your browser
- **API Docs**: Visit http://127.0.0.1:8000/docs (Swagger UI)

### Default Accounts
| Username | Password |
|----------|----------|
| admin    | admin    |
| test     | test     |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | Authenticate and get JWT token |
| GET | `/me` | Get current user's profile |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Register new user |
| GET | `/users/{id}` | Get user profile |
| PUT | `/users/{id}` | Update user (auth required) |
| DELETE | `/users/{id}` | Delete user (auth required) |

### Items
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/items` | List available items with filters |
| POST | `/items` | Create new item (auth required) |
| PUT | `/items/{id}` | Update item (auth required) |
| GET | `/items/seller/{id}` | Get items by seller |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/purchases` | Purchase an item (auth required) |
| POST | `/ratings` | Rate a seller (auth required) |

## GUI Features

### Admin Capabilities (Admin Only)
- **User Controls**: Detailed user lookup, modification, and deletion.
- **Global Item Control**: Ability to change item availability or details.
- **API Playground**: Raw API execution with live JSON feedback.

### Item Filtering
- **Keyword Search**: Search in item names and descriptions
- **Price Range**: Filter by minimum and maximum price

### User Profiles
- Click on a seller's name in the item modal to view their profile
- See all items listed by that seller
- View seller ratings

## License

[MIT](https://choosealicense.com/licenses/mit/)

---

Forked with love by Josh E. SOUSSAN ❤️
