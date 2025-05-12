"""
Regular expression pattern definitions for EJ transaction processing.
These patterns are used to extract information from ATM transaction logs.
"""

import re

# Basic transaction information patterns
TRANSACTION_PATTERNS = {
    "transaction_id": re.compile(r"\*\d+\*"),
    "timestamp": re.compile(r"DATE (\d{2}-\d{2}-\d{2})\s+TIME (\d{2}:\d{2}:\d{2})"),
    "card": re.compile(r"CARD:\s+(\d+\*+\d+)"),
    "amount": re.compile(r"BDT ([\d,]+.\d{2})"),
    "response_code": re.compile(r"RESPONSE CODE\s+:\s+(\d+)"),
    "notes": re.compile(r"DISPENSED\s+([\d\s]+)"),
    "stan_terminal": re.compile(r"(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\d+)\s+(\w+)"),
    "account": re.compile(r"ACCOUNT NBR.\s+:\s+(\d+)"),
    "transaction_number": re.compile(r"TRN. NBR\s+:\s+(\d+)"),
}

# Cash handling patterns
CASH_PATTERNS = {
    "cash_totals": re.compile(r"(DISPENSED|REJECTED|REMAINING)\s+([\d\s]+)"),
    "notes_dispensed_count": re.compile(r"(COUNT|NOTES PRESENTED)\s+(\d+),(\d+),(\d+),(\d+)"),
    "retract_count": re.compile(r"COUNT\s+(\d+),(\d+),(\d+),(\d+)"),
    "deposit_notes": re.compile(r"(\d+) BDT X\s+(\d+) ="),
    "void_notes": re.compile(r"VOID NOTES RETRACTED:(\d+)"),
}

# Deposit-related patterns
DEPOSIT_PATTERNS = {
    "deposit_complete": re.compile(r'CIM-DEPOSIT COMPLETED(.*)'),
    "val": re.compile(r'VAL:\s+(\d{3})'),
}

# Scenario detection patterns
EJ_SCENARIOS = {
    "successful_deposit": re.compile(r"CIM-DEPOSIT COMPLETED.*?VAL:\s*\d+.*?RESPONSE CODE\s*:\s*000", re.DOTALL),
    "deposit_retract": re.compile(r"CASHIN RETRACT STARTED.*?BILLS RETRACTED", re.DOTALL),
    "successful_withdrawal": re.compile(r"(?=.*WITHDRAWAL)(?=.*RESPONSE CODE\s*:\s*000)(?=.*NOTES TAKEN).*", re.DOTALL),
    "withdrawal_retracted": re.compile(r"WITHDRAWAL.*?RETRACT OPERATION.*?NOTES RETRACTED", re.DOTALL),
    "withdrawal_power_loss": re.compile(r"WITHDRAWAL.*?POWER INTERRUPTION DURING DISPENSE", re.DOTALL),
    "transaction_canceled_480": re.compile(r"TRANSACTION CANCELED.*?RESPONSE CODE\s*:\s*480", re.DOTALL),
}

def get_pattern(pattern_type, pattern_name):
    """
    Get a compiled regex pattern by type and name.
    
    Args:
        pattern_type (str): The type of pattern ('transaction', 'cash', 'deposit', 'scenario')
        pattern_name (str): The name of the pattern within that type
        
    Returns:
        re.Pattern: The compiled regular expression pattern
    
    Raises:
        KeyError: If the pattern type or name doesn't exist
    """
    pattern_collections = {
        'transaction': TRANSACTION_PATTERNS,
        'cash': CASH_PATTERNS,
        'deposit': DEPOSIT_PATTERNS,
        'scenario': EJ_SCENARIOS
    }
    
    if pattern_type not in pattern_collections:
        raise KeyError(f"Pattern type '{pattern_type}' not found")
        
    pattern_dict = pattern_collections[pattern_type]
    if pattern_name not in pattern_dict:
        raise KeyError(f"Pattern '{pattern_name}' not found in {pattern_type}")
        
    return pattern_dict[pattern_name]
