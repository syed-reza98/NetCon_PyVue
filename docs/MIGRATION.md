# NetCon Repository Restructuring Migration Guide

## Overview

This document outlines the restructuring of the NetCon PyVue repository to improve maintainability, separation of concerns, and overall project organization.

## Migration Summary

### What Changed

The repository has been restructured from a mixed structure to a clear separation of frontend, backend, and supporting directories:

#### Before Migration
```
NetCon_PyVue/
├── quasar-app/           # Frontend code
├── src/                  # Backend code
├── Docs/                 # Documentation
├── test_*.py            # Test files scattered in root
├── *.json               # Config files in root
└── various other files
```

#### After Migration
```
NetCon_PyVue/
├── frontend/            # All Vue.js/Quasar frontend code
├── backend/             # All Python Flask backend code
├── tests/               # Unified test directory
│   ├── frontend/        # Frontend tests
│   └── backend/         # Backend tests
├── scripts/             # Utility and deployment scripts
├── docs/                # Project documentation
├── config/              # Configuration files
├── README.md            # Updated project overview
└── SECURITY.md          # Security guidelines
```

## Detailed Changes

### 1. Frontend Migration (`quasar-app/` → `frontend/`)

**Files Moved:**
- All contents of `quasar-app/` moved to `frontend/`
- `package.json`, `quasar.config.js`, and all Vue.js source code
- Node modules and build artifacts (excluded from git)

**Impact:**
- No changes to frontend functionality
- Build commands remain the same: `npm run dev`, `npm run build`
- Quasar configuration unchanged

### 2. Backend Migration (`src/` → `backend/`)

**Files Moved:**
- All Python source code from `src/` to `backend/`
- `requirements.txt` and Python dependencies
- Controllers, services, utils, and models directories

**Code Changes:**
- Updated import statements from relative to package-relative imports:
  - `from controllers.ej_controller` → `from .controllers.ej_controller`
  - `from services.ej_service` → `from .services.ej_service`
  - `from models import db` → `from .models import db`
- Added `main.py` as application entry point

### 3. Test Organization

**Files Moved:**
- All `test_*.py` files moved to `tests/backend/`
- Test data files moved to appropriate test directories
- Future frontend tests will go in `tests/frontend/`

**Test Path Updates:**
- Updated Python path in test files to reference new backend structure
- Changed `sys.path.insert(0, 'src')` to `sys.path.insert(0, '../../backend')`

### 4. Documentation Migration (`Docs/` → `docs/`)

**Files Moved:**
- All documentation files moved from `Docs/` to `docs/`
- Maintains lowercase naming convention
- No content changes to existing documentation

### 5. Configuration Organization

**Files Moved:**
- `api.json`, `users.json`, `data.json`, `response.json` → `config/`
- Configuration files now centralized

### 6. Scripts Organization

**Files Moved:**
- `ej_puller/` directory moved to `scripts/ej_puller/`
- Contains log collection and utility scripts

## Updated Workflows

### Development Workflow

#### Backend Development
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py

# Run tests
cd ..
PYTHONPATH=./backend python tests/backend/test_validation.py
```

#### Frontend Development
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Import Statement Changes

If you have any custom scripts or modules that import from the old structure, update them as follows:

#### Old Import Pattern
```python
from src.controllers.ej_controller import ej_controller
from src.services.ej_service import EJService
from src.utils.validators import validate_file_upload
```

#### New Import Pattern
```python
# From within backend directory
from controllers.ej_controller import ej_controller
from services.ej_service import EJService
from utils.validators import validate_file_upload

# From outside backend directory with PYTHONPATH
import sys
sys.path.insert(0, 'backend')
from controllers.ej_controller import ej_controller
```

## Benefits of New Structure

### 1. **Clear Separation of Concerns**
- Frontend and backend code are completely separated
- No confusion about which files belong to which part of the application

### 2. **Improved Maintainability**
- Easier to navigate and understand project structure
- Clear boundaries between different components
- Simplified dependency management

### 3. **Better Development Experience**
- Separate development servers for frontend and backend
- Independent testing and building
- Clearer documentation structure

### 4. **Enhanced Onboarding**
- New developers can easily understand project organization
- Clear README files for each component
- Documented setup procedures

### 5. **Future Scalability**
- Easy to add new services or components
- Microservices-ready structure
- Better CI/CD pipeline organization

## Troubleshooting

### Common Issues

#### Import Errors in Backend
If you encounter import errors:
1. Ensure you're running Python from the correct directory
2. Check that PYTHONPATH includes the backend directory
3. Verify import statements use relative imports within backend

#### Frontend Build Issues
If frontend builds fail:
1. Clear node_modules and reinstall: `rm -rf node_modules && npm install`
2. Clear Quasar cache: `rm -rf .quasar`
3. Check that all files were moved correctly

#### Test Failures
If tests fail to run:
1. Update Python path in test files
2. Ensure test data files are in correct locations
3. Verify backend dependencies are installed

### Rollback Procedure

If issues arise, the migration can be reverted by:
1. Moving files back to original locations
2. Reverting import statement changes
3. Updating test paths back to original structure

However, the new structure is recommended for long-term maintainability.

## Next Steps

### Immediate Actions
1. Update any local development environments
2. Update deployment scripts to use new structure
3. Update CI/CD pipelines if applicable

### Future Improvements
1. Add comprehensive test suites for both frontend and backend
2. Implement Docker containers for each component
3. Add automated deployment scripts in `scripts/` directory
4. Expand documentation in `docs/` directory

## Validation

The migration has been validated by:
- ✅ Backend tests pass with new structure
- ✅ Frontend builds successfully with new structure  
- ✅ Import statements work correctly
- ✅ All files moved to appropriate locations
- ✅ Documentation updated and accurate

## Support

For questions about the migration or issues with the new structure, please:
1. Check this migration guide
2. Review the updated README files
3. Check the troubleshooting section
4. Create an issue if problems persist