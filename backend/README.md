# Backend - Flask API

Python Flask backend providing REST API services for the NetCon application.

## 📁 Structure

```
backend/
├── app/                    # Main application code
│   ├── controllers/        # API route handlers
│   ├── services/          # Business logic services
│   ├── models.py          # Database models
│   ├── app.py            # Flask application entry point
│   └── requirements.txt   # Python dependencies
└── instance/              # Instance-specific files
    └── app.db            # SQLite database
```

## 🚀 Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r app/requirements.txt
   ```

4. **Run the application**
   ```bash
   python app/app.py
   ```

The API will be available at `http://localhost:5000`

## 🔌 API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login

### EJ Services
- `GET /api/ej/` - Hello endpoint
- `POST /api/ej/process` - Process EJ data

## 🗄️ Database

The application uses SQLite for development. The database file is located at `backend/instance/app.db`.

### Models
- **User** - User authentication and profile data
- **Transaction** - Transaction records and processing

## 🧪 Testing

Run tests using pytest:
```bash
python -m pytest tests/
```

## 📦 Dependencies

Key dependencies include:
- **Flask** - Web framework
- **Flask-SQLAlchemy** - Database ORM
- **Flask-CORS** - Cross-origin resource sharing
- **Werkzeug** - Security utilities

See `app/requirements.txt` for complete list.

## 🔧 Configuration

Environment variables (set in `.env` or environment):
- `FLASK_ENV` - Environment mode (development/production)
- `FLASK_DEBUG` - Enable debug mode
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Flask secret key for sessions

## 🚀 Production Deployment

For production deployment:

1. **Set environment variables**
   ```bash
   export FLASK_ENV=production
   export FLASK_DEBUG=false
   export DATABASE_URL=postgresql://user:pass@host:port/db
   ```

2. **Use a production WSGI server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app.app:app
   ```

## 🐛 Troubleshooting

### Common Issues

1. **Database not found**
   - Ensure the `instance/` directory exists
   - Run the app once to create the database

2. **Import errors**
   - Verify virtual environment is activated
   - Check that all dependencies are installed

3. **Port already in use**
   - Change the port in `app.py` or kill the process using port 5000