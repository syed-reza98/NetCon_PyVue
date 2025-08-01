# Frontend - Vue.js/Quasar Application

Modern Vue.js frontend built with Quasar Framework, providing a responsive web interface for the NetCon application.

## 📁 Structure

```
frontend/
├── src/                   # Source code
│   ├── components/        # Vue components
│   ├── layouts/          # Layout components
│   ├── pages/            # Page components
│   ├── router/           # Vue Router configuration
│   ├── stores/           # Pinia stores (state management)
│   ├── boot/             # Boot files (plugins, initialization)
│   └── css/              # Styles
├── public/               # Static assets
├── package.json          # Node.js dependencies
├── quasar.config.js      # Quasar configuration
└── README.md             # This file
```

## 🚀 Setup

### Prerequisites
- Node.js 16+ 
- npm or yarn
- Quasar CLI (installed globally)

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn
   ```

3. **Install Quasar CLI (if not already installed)**
   ```bash
   npm install -g @quasar/cli
   ```

4. **Start development server**
   ```bash
   npm run dev
   # or
   quasar dev
   ```

The application will be available at `http://localhost:8080`

## 🖥️ Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Lint code with ESLint
- `npm run format` - Format code with Prettier
- `quasar dev -m electron` - Start Electron desktop app
- `quasar build` - Build for production
- `quasar build -m electron` - Build Electron app

## 🎨 UI Framework

The application uses **Quasar Framework** which provides:
- Material Design components
- Responsive grid system
- Built-in dark/light mode
- Mobile-first approach
- Cross-platform compatibility

## 🔧 Configuration

### Quasar Configuration
Key configuration options in `quasar.config.js`:
- **Build targets** - Browser compatibility
- **Plugins** - Quasar plugins to include
- **CSS** - Stylesheet imports
- **Electron** - Desktop app settings

## 🚀 Production Build

### Web Application
```bash
quasar build
```
Output: `dist/spa/`

### Electron App
```bash
quasar build -m electron
```
Output: `dist/electron/`

## 🐛 Troubleshooting

### Common Issues

1. **Node modules not found**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Quasar CLI not found**
   ```bash
   npm install -g @quasar/cli
   ```

3. **Build errors**
   - Ensure Node.js version compatibility
   - Clear build cache: `quasar clean`

### Customize the configuration
See [Configuring quasar.config.js](https://v2.quasar.dev/quasar-cli-vite/quasar-config-js).
