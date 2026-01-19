# Marketplace API Boilerplate

This repository is a comprehensive backend application for a Marketplace, built with FastAPI, SQLAlchemy, and SQLite. It implements a secure, scalable architecture with the following layers:

- **Service Layer**: FastAPI API handling HTTP requests and authentication ([main.py](main.py)).
- **Working Layer**: Business logic and core functionality ([app/core](app/core)).
- **Storage Layer**: Database abstraction and ORM modeling ([app/core/db](app/core/db)).

## Key Features

- **User Authentication**: Secure registration and login using PBKDF2 password hashing and JWT (JSON Web Tokens).
- **Marketplace Management**: Full CRUD for Users and Items.
- **Transaction System**: Purchase flow with item status tracking (`AVAILABLE`, `SOLD`, `REMOVED`).
- **Rating System**: Social feedback mechanism where buyers rate sellers, with automatic average rating calculations.
- **Advanced Filtering**: Search items by keywords, price range, and seller reputation.
- **Massive Data Seeding**: Scripts to populate the database with a realistic dataset of 50 users, 200 items, and simulated transaction histories.

## Installation

1. **Environment Setup**:
   Use `uv` to manage the environment and dependencies.

   ```bash
   uv sync
   ```
2. **Configuration**:

   - In `app/conf`, copy `config_template.ini` to `config.ini` and configure your settings.
   - Ensure `logging.ini` is present in the same directory.
3. **Initialize Database**:
   Run the seeding script to create the schema and populate the database with 200+ entities:

   ```bash
   uv run app/utils/initDB.py
   ```

## Usage

Start the development server:

```bash
uv run fastapi dev
```

Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to explore the interactive API documentation (Swagger UI).

### Authentication

Most endpoints require a JWT token. Use the `/login` endpoint to obtain a token, then include it in the `Authorization` header:
`Authorization: Bearer <your_token>`

## Architecture

- `app/core/db/db_manager.py`: Handles complex queries like filtered items and transaction logic.
- `app/core/db/db_model.py`: Defines SQL tables for Users, Items, Transactions, and Ratings.
- `app/core/auth.py`: Contains security logic for tokens and hashing.
- `app/utils/initDB.py`: Scalable script for bulk data generation.

## Contributing

This repository is not opened to contributions at the moment. I strongly advise you to fork this repository and make your own boilerplate : you can add a log manager, modify the data model ...

## License

[MIT](https://choosealicense.com/licenses/mit/)

You can do basically anything using this code, even sell your application and close-source it. However, it comes with no warranty or liability from my side. You use this code at your own risk, and what you do with it is your own responsibility.

## Final advices

- I have made this readme with [makeareadme](https://www.makeareadme.com/) and advise you do the same when you create a new application. A repository without any readme will not be corrected.
- You should include tests in your application when possible
- I have included Python standard gitignore, if some files should not be commited (like a sqlite database ... for example !), you have to update the gitignore because I won't do it for you !
- You can find the conda instructions [here](https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf) if you are lost with virtual environments.
- Do not forget to update the requirements when you add a package : an incomplete package list will break the app and your users won't fix the list for you !
- Thinking and understanding what problem you are trying to solve before coding is not a choice, **it is mandatory**. If you have not done it first, close this repository, close your laptop, take a paper and a pencil and go back to conceiving your app. When the conception phase is finished, and you have a diagram, come back here.

Sincerely

Prof. Sorbus

# Forked with love by Josh E. SOUSSAN ❤️
