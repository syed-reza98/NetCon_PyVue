# NetCon: A Microservices-based Reconciliation System

## Project Overview

NetCon is a comprehensive reconciliation system built with a modern microservices architecture, featuring a Python Flask backend and a Vue.js/Quasar frontend. The system specializes in processing Electronic Journal (EJ) transaction logs from ATM systems with advanced security, validation, and real-time processing capabilities.

## Architecture

This repository is structured as a monorepo with clear separation of concerns:

```
NetCon_PyVue/
├── frontend/              # Vue.js/Quasar frontend application
├── backend/               # Python Flask backend API
├── tests/                 # Test suites for both frontend and backend
│   ├── frontend/          # Frontend tests
│   └── backend/           # Backend tests
├── scripts/               # Utility and deployment scripts
├── docs/                  # Project documentation
├── config/                # Configuration files and data
├── README.md              # This file
└── SECURITY.md            # Security guidelines
```

## Technology Stack

### Backend
- **Python 3.9+** with Flask framework
- **Flask-SQLAlchemy** for database operations
- **Flask-JWT-Extended** for authentication
- **Pandas** for data processing
- **Gunicorn** for production deployment

### Frontend
- **Vue.js 3** with Composition API
- **Quasar Framework** for UI components
- **Pinia** for state management
- **Electron** for desktop application packaging

### Database
- SQLite for development
- PostgreSQL/MySQL for production

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```bash
   python main.py
   ```

The backend API will be available at `http://localhost:5000`.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend application will be available at `http://localhost:8080`.

## Features

### Core Functionality
- **EJ File Processing**: Upload and process Electronic Journal transaction logs
- **Real-time Processing**: Concurrent file processing with progress tracking
- **Data Validation**: Comprehensive input validation and sanitization
- **Transaction Analysis**: Advanced transaction pattern analysis
- **Export Capabilities**: Export processed data in multiple formats

### Security Features
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: API rate limiting to prevent abuse
- **Input Validation**: Comprehensive input sanitization
- **CORS Protection**: Cross-origin request security
- **Password Hashing**: Bcrypt-based password security

### User Interface
- **Responsive Design**: Mobile-first responsive interface
- **Real-time Updates**: Live progress indicators and notifications
- **File Upload**: Drag-and-drop file upload interface
- **Data Visualization**: Transaction data charts and reports
- **Multi-language Support**: Internationalization ready

## Development

### Running Tests

Backend tests:
```bash
cd backend
PYTHONPATH=. python -m pytest ../tests/backend/
```

Frontend tests:
```bash
cd frontend
npm run test
```

### Code Quality

Backend linting:
```bash
cd backend
flake8 .
black .
```

Frontend linting:
```bash
cd frontend
npm run lint
```

### Building for Production

Backend (using Gunicorn):
```bash
cd backend
gunicorn --bind 0.0.0.0:5000 --workers 4 app:create_app()
```

Frontend:
```bash
cd frontend
npm run build
```

## Deployment

### Docker Support
Both frontend and backend can be containerized for easy deployment.

### Electron Desktop App
The frontend can be packaged as a desktop application:
```bash
cd frontend
quasar build -m electron
```

## Documentation

- **[Backend Documentation](./backend/README.md)** - Detailed backend setup and API documentation
- **[Frontend Documentation](./frontend/README.md)** - Frontend development and build instructions
- **[API Documentation](./docs/)** - Complete API reference
- **[Security Guidelines](./SECURITY.md)** - Security best practices and reporting

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the coding standards
4. Run tests to ensure everything works
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Guidelines
- Follow the existing code style and structure
- Write tests for new functionality
- Update documentation for changes
- Use meaningful commit messages
- Ensure all tests pass before submitting

## License

This project is proprietary software. All rights reserved.

## Support

For support and questions, please refer to the documentation or create an issue in the repository.

---

**Note**: This system is designed for processing financial transaction data. Ensure proper security measures and compliance with relevant regulations when deploying in production environments.
