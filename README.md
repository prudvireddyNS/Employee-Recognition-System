
# Employee Recognition System

Face recognition-based attendance system built with FastAPI and React.

## Project Structure

```
.
├── app
│   ├── backend
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── face_recognition.py
│   │   ├── main.py
│   │   ├── middleware.py
│   │   ├── schemas.py
│   │   ├── utils.py
│   │   └── requirements.txt
│   └── frontend
│       ├── public
│       └── src
├── .env
├── .gitignore
└── README.md
```

## Setup Instructions

### Backend

1. **Clone the repository:**
    ```sh
    git clone <repository_url>
    cd <repository_directory>
    ```

2. **Create and activate a virtual environment:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**
    ```sh
    pip install -r app/backend/requirements.txt
    ```

4. **Run the FastAPI server:**
    ```sh
    uvicorn app.backend.main:app --reload
    ```

### Frontend

1. **Navigate to the frontend directory:**
    ```sh
    cd app/frontend
    ```

2. **Install the dependencies:**
    ```sh
    npm install
    ```

3. **Run the React development server:**
    ```sh
    npm start
    ```

## Environment Variables

Create a `.env` file in the root directory and add the following environment variables:

```
SECRET_KEY=<your_secret_key>
REDIS_URL=redis://localhost:6379
SENTRY_DSN=<your_sentry_dsn>
```

## API Documentation

The API documentation is available at `/api/v1/docs` for Swagger UI and `/api/v1/redoc` for ReDoc.

## License

This project is licensed under the MIT License.