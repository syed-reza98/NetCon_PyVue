# NetCon Backend

This directory contains the Python Flask backend API for NetCon.

## Technologies Used

- **Flask** - Lightweight web framework for Python
- **Flask-SQLAlchemy** - SQL toolkit and ORM for Flask
- **Flask-JWT-Extended** - JWT token handling for Flask
- **Flask-CORS** - Cross-Origin Resource Sharing support
- **Flask-Limiter** - Rate limiting for Flask applications
- **Pandas** - Data manipulation and analysis library
- **Marshmallow** - Object serialization/deserialization library
- **Bcrypt** - Password hashing library
- **Gunicorn** - Python WSGI HTTP Server for UNIX

## Directory Structure

```
backend/
├── controllers/           # Request handlers and API endpoints
│   ├── auth_controller.py # Authentication endpoints
│   └── ej_controller.py   # EJ processing endpoints
├── services/             # Business logic layer
│   ├── ej_service.py     # EJ processing service
│   └── ej_service_old.py # Legacy service (deprecated)
├── utils/                # Utility functions and helpers
│   ├── validators.py     # Input validation functions
│   └── security.py       # Security utilities
├── custom_types/         # Custom type definitions
├── logs/                 # Application logs
├── instance/             # Database and instance files
├── app.py                # Flask application factory
├── ej.py                 # Legacy EJ controller
├── models.py             # Database models
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Development

To start the development server:

```bash
python main.py
```

Or using Flask CLI:

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

The API will be available at `http://localhost:5000` by default.

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
HOST=127.0.0.1
```

### Database Setup

Initialize the database:

```bash
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Testing

Tests are located in the `../tests/backend/` directory. Run tests with:

```bash
# From the project root
PYTHONPATH=./backend python tests/backend/test_validation.py
```

For running all tests with pytest (if installed):

```bash
pytest tests/backend/
```

### Production Deployment

For production deployment, use Gunicorn:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 app:create_app()
```

## API Endpoints

### Authentication

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh JWT token
- `GET /api/auth/profile` - Get user profile (requires authentication)

### EJ Processing

- `POST /api/ej/upload` - Upload and process EJ files
- `GET /api/ej/transactions` - Get processed transactions
- `POST /api/ej/process` - Process EJ files from file paths

## Configuration

The application uses a factory pattern with different configurations:

- **Development**: Debug mode enabled, SQLite database
- **Testing**: In-memory database for tests
- **Production**: Optimized settings, external database

## Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting on API endpoints
- Input validation and sanitization
- CORS protection
- SQL injection prevention through ORM

## Database Models

- **User**: User accounts and authentication
- **Transaction**: EJ transaction records
- **Log**: Application and audit logs

## Error Handling

The application includes comprehensive error handling:

- Custom error responses with appropriate HTTP status codes
- Logging of errors and exceptions
- Validation error messages
- Rate limiting responses

## Contributing

1. Follow PEP 8 style guidelines
2. Add docstrings to all functions and classes
3. Write tests for new functionality
4. Use type hints where appropriate
5. Update documentation for API changes