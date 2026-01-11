"""
Improved EJ Controller with enhanced security, error handling, and maintainability.
Handles transaction log processing with proper validation and rate limiting.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from werkzeug.exceptions import BadRequest, InternalServerError
from marshmallow import Schema, fields, ValidationError
import pandas as pd
from datetime import datetime, timezone
import os

from services.ej_service import EJService
from models import db, Transaction
from utils.validators import validate_file_upload, sanitize_filename
from utils.security import check_rate_limit, log_security_event

# Configure limiter (will be initialized in app factory)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

ej_controller = Blueprint('ej_controller', __name__)

class FileUploadSchema(Schema):
    """Schema for validating file uploads"""
    files = fields.List(fields.Raw(), required=True, validate=lambda x: len(x) > 0)

class TransactionQuerySchema(Schema):
    """Schema for transaction query parameters"""
    page = fields.Integer(missing=1, validate=lambda x: x >= 1)
    per_page = fields.Integer(missing=20, validate=lambda x: 1 <= x <= 100)
    start_date = fields.DateTime(missing=None)
    end_date = fields.DateTime(missing=None)
    transaction_type = fields.String(missing=None)
    status = fields.String(missing=None)

# Initialize service
ej_service = EJService()

@ej_controller.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle Marshmallow validation errors"""
    current_app.logger.warning(f"Validation error: {error.messages}")
    return jsonify({
        'error': 'Validation failed',
        'details': error.messages
    }), 400

@ej_controller.errorhandler(BadRequest)
def handle_bad_request(error):
    """Handle bad request errors"""
    current_app.logger.warning(f"Bad request: {error.description}")
    return jsonify({
        'error': 'Bad request',
        'message': error.description
    }), 400

@ej_controller.errorhandler(InternalServerError)
def handle_internal_error(error):
    """Handle internal server errors"""
    current_app.logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

@ej_controller.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check service availability
        service_status = ej_service.health_check()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': 'connected',
            'service': service_status
        }), 200
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e)
        }), 503

@ej_controller.route('/hello', methods=['GET'])
@limiter.limit("10 per minute")
def hello():
    """Simple hello endpoint with rate limiting"""
    return jsonify({
        'message': "Hello from EJ!",
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': current_app.config.get('APP_VERSION', '1.0.0')
    }), 200

@ej_controller.route('/load_logs', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def load_logs():
    """
    Enhanced log processing endpoint with comprehensive validation and error handling.
    
    Returns:
        JSON response with processed transactions or error details
    """
    try:
        # Check trial status first
        if not ej_service.is_trial_active():
            log_security_event('trial_expired_access_attempt', {
                'user_id': get_jwt_identity(),
                'ip_address': request.remote_addr,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return jsonify({
                'error': 'Trial period has expired',
                'message': 'Please contact Networld Technology Limited to extend your trial.',
                'contact_info': {
                    'company': 'Networld Technology Limited',
                    'support_email': 'support@networld.com'
                }
            }), 403

        # Validate request content type
        if 'multipart/form-data' not in request.content_type:
            raise BadRequest('Content-Type must be multipart/form-data')

        # Validate file uploads
        if 'files' not in request.files:
            raise BadRequest('No files provided in request')

        uploaded_files = request.files.getlist("files")
        if not uploaded_files or len(uploaded_files) == 0:
            raise BadRequest('No files uploaded')

        # Validate individual files
        validated_files = []
        total_size = 0
        max_total_size = current_app.config.get('MAX_TOTAL_UPLOAD_SIZE', 50 * 1024 * 1024)  # 50MB
        
        for file in uploaded_files:
            # Validate file
            validation_result = validate_file_upload(file)
            if not validation_result['valid']:
                current_app.logger.warning(f"File validation failed: {validation_result['error']}")
                return jsonify({
                    'error': 'File validation failed',
                    'details': validation_result['error'],
                    'filename': file.filename
                }), 400
            
            # Check total size limit
            file_size = len(file.read())
            file.seek(0)  # Reset file pointer
            total_size += file_size
            
            if total_size > max_total_size:
                raise BadRequest(f'Total upload size exceeds limit of {max_total_size // (1024*1024)}MB')
            
            validated_files.append({
                'file': file,
                'filename': sanitize_filename(file.filename),
                'size': file_size
            })

        current_app.logger.info(f"Processing {len(validated_files)} files, total size: {total_size} bytes")

        # Process files
        log_contents = {}
        processing_errors = []

        for file_data in validated_files:
            file = file_data['file']
            filename = file_data['filename']
            
            try:
                content = file.read().decode("utf-8", errors="ignore")
                lines = content.splitlines()
                log_contents[filename] = lines
                
                current_app.logger.debug(f"Processed file: {filename}, {len(content)} chars, {len(lines)} lines")
                
            except Exception as e:
                error_msg = f"Failed to process file {filename}: {str(e)}"
                current_app.logger.error(error_msg)
                processing_errors.append({
                    'filename': filename,
                    'error': str(e)
                })

        if not log_contents:
            return jsonify({
                'error': 'No files could be processed',
                'processing_errors': processing_errors
            }), 400

        # Process transactions
        try:
            df_all_transactions = ej_service.process_transactions(log_contents)
            
            if df_all_transactions.empty:
                current_app.logger.warning("No transactions extracted from uploaded files")
                return jsonify({
                    'message': 'No transactions found in the uploaded files',
                    'processing_errors': processing_errors,
                    'files_processed': len(log_contents)
                }), 200

            # Filter valid transactions
            valid_transactions = df_all_transactions[
                df_all_transactions[['timestamp', 'card_number', 'transaction_type', 'amount']].notna().any(axis=1)
            ]

            if valid_transactions.empty:
                current_app.logger.warning("No valid transactions after filtering")
                return jsonify({
                    'message': 'No valid transactions found after filtering',
                    'total_extracted': len(df_all_transactions),
                    'processing_errors': processing_errors
                }), 200

            # Convert to JSON format
            transactions_json = valid_transactions.fillna("").to_dict(orient="records")
            
            # Save transactions to database
            saved_count = _save_transactions_to_database(transactions_json)
            
            # Log success
            current_app.logger.info(f"Successfully processed {saved_count} transactions from {len(log_contents)} files")
            
            # Prepare response
            response_data = {
                'status': 'success',
                'summary': {
                    'files_uploaded': len(uploaded_files),
                    'files_processed': len(log_contents),
                    'total_transactions_extracted': len(df_all_transactions),
                    'valid_transactions': len(valid_transactions),
                    'transactions_saved': saved_count,
                    'processing_time': datetime.now(timezone.utc).isoformat()
                },
                'transactions': transactions_json[:100] if len(transactions_json) > 100 else transactions_json  # Limit response size
            }
            
            if processing_errors:
                response_data['processing_errors'] = processing_errors
                
            if len(transactions_json) > 100:
                response_data['note'] = f"Response limited to first 100 transactions. Total: {len(transactions_json)}"

            return jsonify(response_data), 200

        except Exception as e:
            current_app.logger.error(f"Transaction processing failed: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Transaction processing failed',
                'message': str(e),
                'processing_errors': processing_errors
            }), 500

    except BadRequest as e:
        raise e  # Re-raise to be handled by error handler
    except Exception as e:
        current_app.logger.error(f"Unexpected error in load_logs: {str(e)}", exc_info=True)
        raise InternalServerError(f"Unexpected error: {str(e)}")

def _save_transactions_to_database(transactions_json: List[Dict[str, Any]]) -> int:
    """
    Save transactions to database with error handling and batch processing.
    
    Args:
        transactions_json: List of transaction dictionaries
        
    Returns:
        Number of transactions successfully saved
    """
    saved_count = 0
    batch_size = current_app.config.get('DATABASE_BATCH_SIZE', 100)
    
    try:
        for i in range(0, len(transactions_json), batch_size):
            batch = transactions_json[i:i + batch_size]
            
            for tx in batch:
                try:                    # Create transaction object with validation
                    transaction = Transaction(
                        transaction_id=tx.get('transaction_id'),
                        timestamp=_parse_timestamp(tx.get('timestamp')),
                        card_number=tx.get('card_number'),
                        transaction_type=tx.get('transaction_type'),
                        retract=_safe_bool_conversion(tx.get('retract')),
                        no_notes_dispensed=_safe_bool_conversion(tx.get('no_notes_dispensed')),
                        notes_dispensed_unknown=_safe_bool_conversion(tx.get('notes_dispensed_unknown')),
                        amount=_safe_decimal_conversion(tx.get('amount')),
                        response_code=tx.get('response_code'),
                        authentication=_safe_bool_conversion(tx.get('authentication')),
                        pin_entry=_safe_bool_conversion(tx.get('pin_entry')),
                        notes_dispensed=tx.get('notes_dispensed'),
                        notes_dispensed_count=_safe_int_conversion(tx.get('notes_dispensed_count')),
                        notes_dispensed_t1=_safe_int_conversion(tx.get('notes_dispensed_t1')),
                        notes_dispensed_t2=_safe_int_conversion(tx.get('notes_dispensed_t2')),
                        notes_dispensed_t3=_safe_int_conversion(tx.get('notes_dispensed_t3')),
                        notes_dispensed_t4=_safe_int_conversion(tx.get('notes_dispensed_t4')),
                        status=tx.get('status'),
                        stan=tx.get('stan'),
                        terminal=tx.get('terminal'),
                        account_number=tx.get('account_number'),
                        transaction_number=tx.get('transaction_number'),
                        cash_dispensed=_safe_decimal_conversion(tx.get('cash_dispensed')),
                        cash_rejected=_safe_decimal_conversion(tx.get('cash_rejected')),
                        cash_remaining=_safe_decimal_conversion(tx.get('cash_remaining')),
                        number_of_total_inserted_notes=_safe_int_conversion(tx.get('Number of Total Inserted Notes')),
                        note_count_bdt500=_safe_int_conversion(tx.get('Note_Count_BDT500')),
                        note_count_bdt1000=_safe_int_conversion(tx.get('Note_Count_BDT1000')),
                        bdt500_abox=_safe_int_conversion(tx.get('BDT500_ABOX')),
                        bdt500_type1=_safe_int_conversion(tx.get('BDT500_TYPE1')),
                        bdt500_type2=_safe_int_conversion(tx.get('BDT500_TYPE2')),
                        bdt500_type3=_safe_int_conversion(tx.get('BDT500_TYPE3')),
                        bdt500_type4=_safe_int_conversion(tx.get('BDT500_TYPE4')),
                        bdt500_retract=_safe_int_conversion(tx.get('BDT500_RETRACT')),
                        bdt500_reject=_safe_int_conversion(tx.get('BDT500_REJECT')),
                        bdt500_retract2=_safe_int_conversion(tx.get('BDT500_RETRACT2')),
                        bdt1000_abox=_safe_int_conversion(tx.get('BDT1000_ABOX')),
                        bdt1000_type1=_safe_int_conversion(tx.get('BDT1000_TYPE1')),
                        bdt1000_type2=_safe_int_conversion(tx.get('BDT1000_TYPE2')),
                        bdt1000_type3=_safe_int_conversion(tx.get('BDT1000_TYPE3')),
                        bdt1000_type4=_safe_int_conversion(tx.get('BDT1000_TYPE4')),
                        bdt1000_retract=_safe_int_conversion(tx.get('BDT1000_RETRACT')),
                        bdt1000_reject=_safe_int_conversion(tx.get('BDT1000_REJECT')),
                        bdt1000_retract2=_safe_int_conversion(tx.get('BDT1000_RETRACT2')),
                        total_abox=_safe_int_conversion(tx.get('TOTAL_ABOX')),
                        total_type1=_safe_int_conversion(tx.get('TOTAL_TYPE1')),
                        total_type2=_safe_int_conversion(tx.get('TOTAL_TYPE2')),
                        total_type3=_safe_int_conversion(tx.get('TOTAL_TYPE3')),
                        total_type4=_safe_int_conversion(tx.get('TOTAL_TYPE4')),
                        total_retract=_safe_int_conversion(tx.get('TOTAL_RETRACT')),
                        total_reject=_safe_int_conversion(tx.get('TOTAL_REJECT')),
                        total_retract2=_safe_int_conversion(tx.get('TOTAL_RETRACT2')),
                        result=tx.get('result'),
                        scenario=tx.get('scenario'),
                        retract_type1=_safe_int_conversion(tx.get('retract_type1')),
                        retract_type2=_safe_int_conversion(tx.get('retract_type2')),
                        retract_type3=_safe_int_conversion(tx.get('retract_type3')),
                        retract_type4=_safe_int_conversion(tx.get('retract_type4')),
                        total_retracted_notes=_safe_int_conversion(tx.get('total_retracted_notes')),
                        deposit_retract_100=_safe_int_conversion(tx.get('deposit_retract_100')),
                        deposit_retract_500=_safe_int_conversion(tx.get('deposit_retract_500')),
                        deposit_retract_1000=_safe_int_conversion(tx.get('deposit_retract_1000')),
                        deposit_retract_unknown=_safe_int_conversion(tx.get('deposit_retract_unknown')),
                        total_deposit_retracted=_safe_int_conversion(tx.get('total_deposit_retracted')),
                        file_name=tx.get('file_name'),
                        ej_log=str(tx.get('ej_log')) if tx.get('ej_log') is not None else None,
                        processed_by=get_jwt_identity()
                    )
                    
                    db.session.add(transaction)
                    saved_count += 1
                    
                except Exception as e:
                    current_app.logger.error(f"Failed to create transaction object: {str(e)}")
                    continue
            
            # Commit batch
            try:
                db.session.commit()
                current_app.logger.debug(f"Committed batch {i//batch_size + 1}, saved {len(batch)} transactions")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Failed to commit batch {i//batch_size + 1}: {str(e)}")
                saved_count -= len(batch)  # Adjust count for failed batch
                
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database save operation failed: {str(e)}")
        raise

    return saved_count

# Utility functions for safe data conversion
def _safe_int_conversion(value: Any) -> Optional[int]:
    """Safely convert value to integer"""
    if value is None or value == '':
        return None
    try:
        return int(float(str(value)))  # Handle decimal strings
    except (ValueError, TypeError):
        return None

def _safe_decimal_conversion(value: Any) -> Optional[float]:
    """Safely convert value to decimal"""
    if value is None or value == '':
        return None
    try:
        # Remove commas from numbers
        if isinstance(value, str):
            value = value.replace(',', '')
        return float(value)
    except (ValueError, TypeError):
        return None

def _safe_bool_conversion(value: Any) -> bool:
    """Safely convert value to boolean"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)

def _parse_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
    """Parse timestamp string to datetime object"""
    if not timestamp_str:
        return None
    
    # Common timestamp formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%d-%m-%y %H:%M:%S',
        '%m/%d/%y %H:%M:%S',
        '%Y-%m-%d',
        '%d-%m-%y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    current_app.logger.warning(f"Unable to parse timestamp: {timestamp_str}")
    return None

@ej_controller.route('/transactions', methods=['GET'])
@jwt_required()
@limiter.limit("10 per minute")
def get_transactions():
    """
    Get transactions with pagination and filtering.
    
    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
        - start_date: Filter transactions after this date
        - end_date: Filter transactions before this date
        - transaction_type: Filter by transaction type
        - status: Filter by status
    """
    try:
        # Validate query parameters
        schema = TransactionQuerySchema()
        args = schema.load(request.args)
        
        # Build query
        query = Transaction.query
        
        if args.get('start_date'):
            query = query.filter(Transaction.timestamp >= args['start_date'])
        if args.get('end_date'):
            query = query.filter(Transaction.timestamp <= args['end_date'])
        if args.get('transaction_type'):
            query = query.filter(Transaction.transaction_type == args['transaction_type'])
        if args.get('status'):
            query = query.filter(Transaction.status == args['status'])
        
        # Order by timestamp descending
        query = query.order_by(Transaction.timestamp.desc())
        
        # Paginate
        paginated = query.paginate(
            page=args['page'],
            per_page=args['per_page'],
            error_out=False
        )
        
        # Convert to dictionary
        transactions = []
        for tx in paginated.items:
            tx_dict = {
                'id': tx.id,
                'transaction_id': tx.transaction_id,
                'timestamp': tx.timestamp.isoformat() if tx.timestamp else None,
                'card_number': tx.card_number,
                'transaction_type': tx.transaction_type,
                'amount': float(tx.amount) if tx.amount else None,
                'status': tx.status,
                'scenario': tx.scenario,
                'file_name': tx.file_name,
                'created_at': tx.created_at.isoformat() if tx.created_at else None
            }
            transactions.append(tx_dict)
        
        return jsonify({
            'transactions': transactions,
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Invalid query parameters',
            'details': e.messages
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error fetching transactions: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch transactions',
            'message': str(e)
        }), 500

@ej_controller.route('/transactions/<int:transaction_id>', methods=['GET'])
@jwt_required()
@limiter.limit("20 per minute")
def get_transaction(transaction_id):
    """Get detailed transaction information by ID"""
    try:
        transaction = Transaction.query.get_or_404(transaction_id)
        
        # Convert to detailed dictionary
        tx_dict = transaction.to_dict()
        
        return jsonify({
            'transaction': tx_dict
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching transaction {transaction_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch transaction',
            'message': str(e)
        }), 500

@ej_controller.route('/statistics/summary', methods=['GET'])
@jwt_required()
@limiter.limit("5 per minute")
def get_transaction_statistics():
    """Get transaction statistics and summary"""
    try:
        # Basic counts
        total_transactions = Transaction.query.count()
        
        # Count by transaction type
        type_counts = db.session.query(
            Transaction.transaction_type,
            db.func.count(Transaction.id).label('count')
        ).group_by(Transaction.transaction_type).all()
        
        # Count by scenario
        scenario_counts = db.session.query(
            Transaction.scenario,
            db.func.count(Transaction.id).label('count')
        ).group_by(Transaction.scenario).all()
        
        # Recent transactions (last 24 hours)
        recent_cutoff = datetime.now(timezone.utc) - pd.Timedelta(hours=24)
        recent_count = Transaction.query.filter(
            Transaction.created_at >= recent_cutoff
        ).count()
        
        return jsonify({
            'summary': {
                'total_transactions': total_transactions,
                'recent_transactions_24h': recent_count,
                'last_updated': datetime.now(timezone.utc).isoformat()
            },
            'by_type': {tc.transaction_type: tc.count for tc in type_counts},
            'by_scenario': {sc.scenario: sc.count for sc in scenario_counts}
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error generating statistics: {str(e)}")
        return jsonify({
            'error': 'Failed to generate statistics',
            'message': str(e)
        }), 500
