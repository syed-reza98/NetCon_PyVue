# Flask API Project

This project is a Flask-based API designed to process transactions and handle logs. It provides endpoints for uploading log files, processing transactions, and retrieving transaction data.

## Project Structure

```
PythonQuasarElectron
├── src
│   ├── app.py                  # Entry point of the Flask application
│   ├── ej.py                   # Original logic for processing transactions  
│   ├── controllers             # Contains controllers for handling API requests
│   │   └── ej_controller.py    # Controller for transaction processing
│   ├── services                # Contains business logic for the application
│   │   └── ej_service.py       # Service for processing transactions and logs
│   └── custom_types            # Custom types or data models
│       └── __init__.py
├── requirements.txt            # Lists project dependencies
└── README.md                   # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd flask-api-project
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. **Install the required packages:**
   ```
   pip install -r requirements.txt
   ```

## Usage

1. **Run the Flask application:**
   ```
   python src/app.py
   ```

2. **API Endpoints:**
   - **Upload Log File:**
     - `POST /api/upload`
     - Description: Upload a log file for processing.
     - Request Body: Multipart form data containing the log file.

   - **Process Transactions:**
     - `GET /api/transactions`
     - Description: Retrieve processed transaction data.

   - **Get Transaction Details:**
     - `GET /api/transactions/<transaction_id>`
     - Description: Get details of a specific transaction by ID.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.