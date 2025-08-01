# Electron Desktop Application

Configuration and setup for the NetCon Electron desktop application.

## 📁 Structure

```
electron/
├── electron-main.js       # Main Electron process
├── electron-preload.js    # Preload script for renderer process  
├── icons/                 # Application icons
└── python/                # Python executable and dependencies
```

## 🚀 Setup

The Electron configuration is integrated with the Quasar frontend. To run the desktop application:

### Prerequisites
- Node.js 16+
- Python 3.8+ (for backend executable)
- Completed frontend setup

### Development Mode

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies** (if not already done)
   ```bash
   npm install
   ```

3. **Start Electron development mode**
   ```bash
   quasar dev -m electron
   ```

This will:
- Start the Vue.js development server
- Launch the Electron window
- Start the Python backend process
- Enable hot reloading for frontend changes

## 🔧 Configuration

### Main Process (`electron-main.js`)

The main process handles:
- **Window Management** - Creating and managing application windows
- **Python Process** - Starting and stopping the Flask backend
- **System Integration** - OS-level interactions and tray management
- **Security** - Context isolation and preload scripts

Key features:
- Automatic Python backend startup/shutdown
- Process cleanup on application exit
- Development/production path handling
- Error handling and logging

### Preload Script (`electron-preload.js`)

Provides secure communication between main and renderer processes:
- Exposes limited APIs to the frontend
- Maintains security through context isolation
- Handles IPC (Inter-Process Communication)

## 🏗️ Build Process

### Development Build
```bash
cd frontend
quasar dev -m electron
```

### Production Build
```bash
cd frontend
quasar build -m electron
```

Output: `frontend/dist/electron/`

The build process:
1. Builds the Vue.js frontend
2. Packages the Electron application
3. Includes the Python executable
4. Creates platform-specific installers

## 📦 Distribution

### Windows
- **Output**: `.exe` installer
- **Location**: `frontend/dist/electron/Packaged/`

### macOS  
- **Output**: `.dmg` disk image
- **Location**: `frontend/dist/electron/Packaged/`

### Linux
- **Output**: `.AppImage` or distribution packages
- **Location**: `frontend/dist/electron/Packaged/`

## 🔧 Configuration Options

### Electron Builder Settings

Located in `frontend/quasar.config.js`:

```javascript
electron: {
  bundler: 'builder',
  builder: {
    appId: 'com.yourcompany.netcon',
    productName: 'NetCon',
    extraFiles: [
      { from: '../dist', to: 'dist' }
    ],
    win: {
      target: 'nsis',
      icon: '../electron/icons/icon.ico',
    }
  }
}
```

### Path Configuration

The application automatically handles different path configurations:
- **Development**: Relative paths to source files
- **Production**: Packaged resource paths

## 🐛 Troubleshooting

### Common Issues

1. **Python process not starting**
   - Check if executable exists in `../dist/`
   - Verify executable permissions
   - Check console logs for error messages

2. **Build failures**
   - Ensure all dependencies are installed
   - Check Node.js version compatibility
   - Clear build cache: `quasar clean`

3. **Window not appearing**
   - Check if another instance is running
   - Verify display/screen configuration
   - Check console for JavaScript errors

4. **IPC communication issues**
   - Verify preload script is loaded
   - Check context isolation settings
   - Review security policies

### Debugging

Enable debug mode by setting environment variables:
```bash
DEBUGGING=true quasar dev -m electron
```

This will:
- Open Developer Tools automatically
- Enable verbose logging
- Show additional debug information

## 🔒 Security

The Electron configuration follows security best practices:
- **Context Isolation** - Enabled to prevent code injection
- **Node Integration** - Disabled in renderer process
- **Preload Scripts** - Used for secure API exposure
- **Process Separation** - Main and renderer processes isolated

## 🚀 Performance

Optimization features:
- **Process Management** - Proper cleanup of Python processes
- **Memory Management** - Efficient window lifecycle
- **Resource Bundling** - Optimized asset packaging
- **Lazy Loading** - Components loaded on demand

## 📋 Development Tips

1. **Hot Reloading**: Frontend changes are automatically reflected
2. **Process Monitoring**: Check console for Python process status
3. **DevTools**: Use Electron DevTools for debugging
4. **Logging**: Enable verbose logging for troubleshooting