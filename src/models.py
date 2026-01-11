"""
Improved Database Models with Validation and Optimization
Author: NetCon Development Team
Date: June 15, 2025
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, CheckConstraint, Numeric
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
import re

db = SQLAlchemy()

class BaseModel(db.Model):
    """Base model with common fields and methods"""
    __abstract__ = True
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def to_dict(self, exclude_fields=None):
        """Convert model to dictionary"""
        exclude_fields = exclude_fields or []
        return {c.name: getattr(self, c.name) 
                for c in self.__table__.columns 
                if c.name not in exclude_fields}

class User(BaseModel):
    """Enhanced User model with validation and security"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime, nullable=True)
    
    # Role-based access control
    role = db.Column(db.String(50), default='user', nullable=False)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='processed_by_user', lazy='dynamic')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('length(email) >= 5', name='email_min_length'),
        CheckConstraint('length(username) >= 3', name='username_min_length'),
        CheckConstraint("role IN ('admin', 'user', 'analyst')", name='valid_role'),
        Index('idx_user_email_active', 'email', 'is_active'),
    )
    
    @hybrid_property
    def password(self):
        """Password property (write-only)"""
        raise AttributeError('Password is not readable')
    
    @password.setter
    def password(self, password):
        """Set password with validation"""
        if not self.validate_password(password):
            raise ValueError('Password does not meet requirements')
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True
    
    @property
    def is_locked(self):
        """Check if account is locked"""
        if self.account_locked_until:
            return datetime.now(timezone.utc) < self.account_locked_until
        return False
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock if needed"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            # Lock account for 30 minutes
            self.account_locked_until = datetime.now(timezone.utc).replace(minute=30)
    
    def reset_failed_login(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.last_login = datetime.now(timezone.utc)
    
    def to_dict(self, exclude_fields=None):
        """Override to exclude sensitive fields"""
        exclude_fields = exclude_fields or ['password_hash', 'failed_login_attempts']
        return super().to_dict(exclude_fields)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Transaction(BaseModel):
    """Enhanced Transaction model with proper data types and validation"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Core Transaction Fields
    transaction_id = db.Column(db.String(100), index=True)
    timestamp = db.Column(db.DateTime, index=True)
    card_number = db.Column(db.String(50))  # Masked card number
    transaction_type = db.Column(db.String(50), index=True)
    
    # Transaction Status
    status = db.Column(db.String(100), default="Unknown")
    scenario = db.Column(db.String(100), default="Unknown", index=True)
    response_code = db.Column(db.String(10), index=True)
      # Financial Fields
    amount = db.Column(Numeric(15, 2))  # Changed from String to Numeric
    cash_dispensed = db.Column(Numeric(15, 2))
    cash_rejected = db.Column(Numeric(15, 2))
    cash_remaining = db.Column(Numeric(15, 2))
    
    # Boolean Flags
    authentication = db.Column(db.Boolean, default=False)
    pin_entry = db.Column(db.Boolean, default=False)
    retract = db.Column(db.Boolean, default=False)
    no_notes_dispensed = db.Column(db.Boolean, default=False)
    notes_dispensed_unknown = db.Column(db.Boolean, default=False)
    
    # Terminal Information
    stan = db.Column(db.String(50), index=True)  # System Trace Audit Number
    terminal = db.Column(db.String(50), index=True)
    account_number = db.Column(db.String(50))  # Encrypted/Masked
    transaction_number = db.Column(db.String(50))
    
    # Notes Dispensing Information
    notes_dispensed = db.Column(db.String(200))
    notes_dispensed_count = db.Column(db.Integer, default=0)
    notes_dispensed_t1 = db.Column(db.Integer, default=0)
    notes_dispensed_t2 = db.Column(db.Integer, default=0)
    notes_dispensed_t3 = db.Column(db.Integer, default=0)
    notes_dispensed_t4 = db.Column(db.Integer, default=0)
    
    # Denomination Tracking - BDT 500
    bdt500_abox = db.Column(db.Integer, default=0)
    bdt500_type1 = db.Column(db.Integer, default=0)
    bdt500_type2 = db.Column(db.Integer, default=0)
    bdt500_type3 = db.Column(db.Integer, default=0)
    bdt500_type4 = db.Column(db.Integer, default=0)
    bdt500_retract = db.Column(db.Integer, default=0)
    bdt500_reject = db.Column(db.Integer, default=0)
    bdt500_retract2 = db.Column(db.Integer, default=0)
    
    # Denomination Tracking - BDT 1000
    bdt1000_abox = db.Column(db.Integer, default=0)
    bdt1000_type1 = db.Column(db.Integer, default=0)
    bdt1000_type2 = db.Column(db.Integer, default=0)
    bdt1000_type3 = db.Column(db.Integer, default=0)
    bdt1000_type4 = db.Column(db.Integer, default=0)
    bdt1000_retract = db.Column(db.Integer, default=0)
    bdt1000_reject = db.Column(db.Integer, default=0)
    bdt1000_retract2 = db.Column(db.Integer, default=0)
    
    # Total Tracking
    total_abox = db.Column(db.Integer, default=0)
    total_type1 = db.Column(db.Integer, default=0)
    total_type2 = db.Column(db.Integer, default=0)
    total_type3 = db.Column(db.Integer, default=0)
    total_type4 = db.Column(db.Integer, default=0)
    total_retract = db.Column(db.Integer, default=0)
    total_reject = db.Column(db.Integer, default=0)
    total_retract2 = db.Column(db.Integer, default=0)
    
    # Deposit Specific Fields
    number_of_total_inserted_notes = db.Column(db.Integer, default=0)
    note_count_bdt500 = db.Column(db.Integer, default=0)
    note_count_bdt1000 = db.Column(db.Integer, default=0)
    
    # Retraction Information
    retract_type1 = db.Column(db.Integer, default=0)
    retract_type2 = db.Column(db.Integer, default=0)
    retract_type3 = db.Column(db.Integer, default=0)
    retract_type4 = db.Column(db.Integer, default=0)
    total_retracted_notes = db.Column(db.Integer, default=0)
    
    # Deposit Retraction
    deposit_retract_100 = db.Column(db.Integer, default=0)
    deposit_retract_500 = db.Column(db.Integer, default=0)
    deposit_retract_1000 = db.Column(db.Integer, default=0)
    deposit_retract_unknown = db.Column(db.Integer, default=0)
    total_deposit_retracted = db.Column(db.Integer, default=0)
    
    # Processing Information
    file_name = db.Column(db.String(500))
    ej_log = db.Column(db.Text)  # Raw EJ log data
    result = db.Column(db.String(200))
    
    # Processing Metadata
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    processing_time = db.Column(db.Float)  # Time taken to process in seconds
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_transaction_timestamp', 'timestamp'),
        Index('idx_transaction_type_status', 'transaction_type', 'status'),
        Index('idx_transaction_scenario', 'scenario'),
        Index('idx_transaction_response_code', 'response_code'),
        Index('idx_transaction_terminal_date', 'terminal', 'timestamp'),
        Index('idx_transaction_file', 'file_name'),        CheckConstraint('amount >= 0', name='positive_amount'),
        CheckConstraint('total_retracted_notes >= 0', name='positive_retracted'),
    )

    @hybrid_property
    def total_bdt500_notes(self):
        """Calculate total BDT 500 notes"""
        return (self.bdt500_abox or 0) + (self.bdt500_type1 or 0) + \
               (self.bdt500_type2 or 0) + (self.bdt500_type3 or 0) + (self.bdt500_type4 or 0)
    
    @hybrid_property
    def total_bdt1000_notes(self):
        """Calculate total BDT 1000 notes"""
        return (self.bdt1000_abox or 0) + (self.bdt1000_type1 or 0) + \
               (self.bdt1000_type2 or 0) + (self.bdt1000_type3 or 0) + (self.bdt1000_type4 or 0)
    
    @hybrid_property
    def total_cash_value(self):
        """Calculate total cash value"""
        return (self.total_bdt500_notes * 500) + (self.total_bdt1000_notes * 1000)
    
    @property
    def is_successful(self):
        """Check if transaction was successful"""
        return self.response_code == '000' and self.scenario in [
            'successful_withdrawal', 'successful_deposit'
        ]

    @property
    def has_anomaly(self):
        """Check if transaction has anomalies"""
        return self.scenario in [
            'withdrawal_retracted', 'deposit_retract', 'transaction_canceled_480'
        ] or (self.total_retracted_notes is not None and self.total_retracted_notes > 0)
    
    def to_dict(self, include_ej_log=False):
        """Convert to dictionary with optional EJ log inclusion"""
        exclude_fields = [] if include_ej_log else ['ej_log']
        data = super().to_dict(exclude_fields)
        
        # Add computed properties
        data.update({
            'total_bdt500_notes': self.total_bdt500_notes,
            'total_bdt1000_notes': self.total_bdt1000_notes,
            'total_cash_value': float(self.total_cash_value) if self.total_cash_value else 0,
            'is_successful': self.is_successful,
            'has_anomaly': self.has_anomaly
        })
        
        return data
    
    @staticmethod
    def get_by_date_range(start_date, end_date):
        """Get transactions by date range"""
        return Transaction.query.filter(
            Transaction.timestamp >= start_date,
            Transaction.timestamp <= end_date
        ).order_by(Transaction.timestamp.desc())
    
    @staticmethod
    def get_by_terminal(terminal_id):
        """Get transactions by terminal"""
        return Transaction.query.filter_by(terminal=terminal_id)\
                                .order_by(Transaction.timestamp.desc())
    
    @staticmethod
    def get_anomalies():
        """Get transactions with anomalies"""
        return Transaction.query.filter(
            Transaction.total_retracted_notes > 0
        ).order_by(Transaction.timestamp.desc())
    
    def __repr__(self):
        return f'<Transaction {self.transaction_id}>'

# Performance Views for Analytics
class TransactionSummary(db.Model):
    """Materialized view for transaction analytics"""
    __tablename__ = 'transaction_summary'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, index=True)
    terminal = db.Column(db.String(50), index=True)
    transaction_type = db.Column(db.String(50), index=True)
    total_transactions = db.Column(db.Integer)
    successful_transactions = db.Column(db.Integer)
    failed_transactions = db.Column(db.Integer)
    total_amount = db.Column(Numeric(15, 2))
    total_dispensed = db.Column(Numeric(15, 2))
    total_retracted = db.Column(db.Integer)
    
    __table_args__ = (
        Index('idx_summary_date_terminal', 'date', 'terminal'),
    )
