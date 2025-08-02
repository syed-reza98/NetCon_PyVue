# NetCon Frontend

This directory contains the Vue.js/Quasar frontend application for NetCon.

## Technologies Used

- **Vue.js 3** - Progressive JavaScript framework
- **Quasar Framework** - Vue.js based framework for building UIs
- **Pinia** - State management library for Vue
- **Axios** - HTTP client for API communication
- **Vue Router** - Official router for Vue.js
- **Vue I18n** - Internationalization plugin for Vue.js

## Directory Structure

```
frontend/
├── src/                    # Source code
│   ├── components/         # Reusable Vue components
│   ├── layouts/           # Layout components
│   ├── pages/             # Page components
│   ├── stores/            # Pinia stores for state management
│   ├── router/            # Vue Router configuration
│   ├── boot/              # App initialization code
│   └── i18n/              # Internationalization files
├── public/                # Static assets
├── src-electron/          # Electron-specific code (if using Electron mode)
├── dist/                  # Build output directory
├── package.json           # Dependencies and scripts
├── quasar.config.js       # Quasar framework configuration
└── README.md              # This file
```

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

### Development

To start the development server:

```bash
npm run dev
```

This will start the Quasar development server at `http://localhost:8080` (by default).

### Building

To build the application for production:

```bash
npm run build
```

The built files will be in the `dist/spa` directory.

### Linting

To run ESLint:

```bash
npm run lint
```

### Testing

Tests are located in the `../tests/frontend/` directory. Currently, no specific test runner is configured, but you can add Jest, Vitest, or Cypress as needed.

## Configuration

- **quasar.config.js**: Main Quasar framework configuration
- **src/router/routes.js**: Route definitions
- **src/stores/**: Pinia store definitions
- **src/boot/**: App initialization plugins

## API Integration

The frontend communicates with the backend API located at `../backend/`. API calls are handled through Axios with configuration in `src/boot/axios.js`.

## Electron Mode

This project is set up to work with Quasar's Electron mode for desktop application packaging. Electron-specific code is in the `src-electron/` directory.

## Contributing

1. Follow the existing code style and structure
2. Use ESLint and Prettier for code formatting
3. Create reusable components in the `components/` directory
4. Use Pinia stores for state management
5. Follow Vue.js composition API best practices
