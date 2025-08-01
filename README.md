# NetCon: Microservices-based Reconciliation System

A modern modular application built with Python Flask backend, Vue.js/Quasar frontend, and Electron desktop packaging.

## 🏗️ Project Structure

```
NetCon_PyVue/
├── backend/                 # Flask API backend
│   ├── app/                # Application code
│   └── instance/           # Database and instance files
├── frontend/               # Vue.js/Quasar frontend
├── electron/               # Electron desktop app configuration
├── dist/                   # Compiled executables and build artifacts
├── docs/                   # Documentation
├── .env.example           # Environment variables template
└── docker-compose.yml     # Development environment setup
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd NetCon_PyVue
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r app/requirements.txt
   python app/app.py
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Electron Desktop App**
   ```bash
   cd frontend
   quasar dev -m electron
   ```

### Using Docker Compose

For a unified development environment:

```bash
docker-compose up --build
```

This will start:
- Backend API on http://localhost:5000
- Frontend on http://localhost:8080
- Electron app with GUI

## 📁 Module Documentation

- **[Backend](backend/README.md)** - Flask API, models, and services
- **[Frontend](frontend/README.md)** - Vue.js/Quasar application  
- **[Electron](electron/README.md)** - Desktop app configuration
- **[Documentation](docs/)** - Additional project documentation

## 🔧 Available Scripts

### Backend
- `python backend/app/app.py` - Start Flask development server
- `python -m pytest backend/tests/` - Run backend tests

### Frontend  
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Lint code
- `quasar dev -m electron` - Start Electron app

### Docker
- `docker-compose up` - Start all services
- `docker-compose down` - Stop all services
- `docker-compose build` - Rebuild containers

## 🛠️ Technology Stack

- **Backend**: Python Flask, SQLAlchemy, SQLite
- **Frontend**: Vue.js 3, Quasar Framework, Vite
- **Desktop**: Electron
- **Database**: SQLite (development), configurable for production
- **Containerization**: Docker & Docker Compose

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the [documentation](docs/) 
- Review existing issues and discussions