# NetCon_PyVue Backend Service

This directory contains the Python Flask backend for the NetCon_PyVue application, which processes Electronic Journal (EJ) files from ATMs.

## Project Structure

- `app.py` - Main Flask application entry point
- `ej.py` - Core EJ processing functionality
- `controllers/` - HTTP route handlers
- `services/` - Business logic
- `config/` - Configuration settings and regex patterns
- `tests/` - Unit tests
- `__pycache__/` - Python compiled bytecode files

## Key Services

### EJService (`services/ej_service.py`)

The `EJService` class is responsible for processing and analyzing ATM transaction logs. It has the following features:

- Loading and merging EJ log files
- Extracting transaction details with pattern matching
- Detecting transaction scenarios (withdrawals, deposits, retracts)
- Detailed analysis of cash handling data

### Key Methods

- `load_logs(file_paths)`: Load multiple log files in parallel
- `process_transactions(log_contents)`: Extract structured data from logs
- `segment_transactions(lines)`: Break log files into individual transactions
- `extract_transaction_details(transaction)`: Extract all data points from a transaction
- `detect_scenario(transaction)`: Identify the transaction type
- `merge_files(file_paths, output_path)`: Merge multiple EJ log files

## Recent Improvements

1. **Code Organization**:
   - Refactored large methods into smaller, focused functions
   - Added helper methods for specific transaction scenarios
   - Created specialized methods for different transaction types
   - Extracted regex patterns to separate configuration file

2. **Error Handling**:
   - Added bounds checking for array access
   - Added exception handling throughout the code
   - Implemented safe default values
   - Added comprehensive error handling for deposit note processing

3. **Configuration**:
   - Moved hard-coded values to central configuration
   - Made trial period configurable
   - Created centralized regex pattern management
   - Implemented a config module with standardized access methods

4. **Documentation**:
   - Added comprehensive docstrings
   - Improved comments for complex code sections
   - Created detailed README documentation

5. **Testing**:
   - Added unit tests for core functionality
   - Created test fixtures for different transaction types
   - Implemented mock objects for external dependencies

## Usage

The service exposes a REST API through `app.py` which can be used by the frontend to:
- Upload and process EJ log files
- Search and filter transactions
- View detailed transaction information

## Dependencies

See `requirements.txt` for a list of Python dependencies.
