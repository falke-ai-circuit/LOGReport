import re
import logging

logger = logging.getLogger(__name__)

# Define regex patterns for actual error responses
BASE_ERROR_PATTERNS = [ # Renamed to BASE_ERROR_PATTERNS
    # General error patterns
    re.compile(r'\berror\b', re.IGNORECASE),
    re.compile(r'\bfailure\b', re.IGNORECASE),
    re.compile(r'\bexception\b', re.IGNORECASE),
    re.compile(r'\btimeout\b', re.IGNORECASE),
    re.compile(r'\bnot found\b', re.IGNORECASE),
    re.compile(r'\bnot supported\b', re.IGNORECASE),
    re.compile(r'\binvalid\b', re.IGNORECASE),
    re.compile(r'command not found', re.IGNORECASE), # Specific error message patterns
    re.compile(r'syntax error', re.IGNORECASE),
    re.compile(r'permission denied', re.IGNORECASE),
    re.compile(r'access denied', re.IGNORECASE),
    re.compile(r'connection refused', re.IGNORECASE),
    re.compile(r'connection failed', re.IGNORECASE),
    re.compile(r'connection timeout', re.IGNORECASE),
    re.compile(r'network error', re.IGNORECASE),
    re.compile(r'authentication failed', re.IGNORECASE),
    re.compile(r'login failed', re.IGNORECASE),
    re.compile(r'error\s*\d+', re.IGNORECASE), # Error codes
    re.compile(r'err\s*\d+', re.IGNORECASE),
]

# Define patterns for valid responses that should NOT be considered errors
VALID_RESPONSE_PATTERNS = [
    re.compile(r'int from fbc rupi counters \d+', re.IGNORECASE),
    re.compile(r'Getting FIELD BUS error counters from RUPI\(\d+\) from FBC agent \d+', re.IGNORECASE),
    re.compile(r'pic\s+IREX ERROR\s+POLL ERROR\s+RESP FAIL\s+IREX COUNT\s+TIMEOUT', re.IGNORECASE),
    re.compile(r'\bok\b', re.IGNORECASE),
    re.compile(r'\bsuccess\b', re.IGNORECASE),
    re.compile(r'\bcompleted\b', re.IGNORECASE),
    re.compile(r'\bdone\b', re.IGNORECASE),
    re.compile(r'\bfinished\b', re.IGNORECASE),
]

# Specific pattern for "Unknown command: 0" that should be ignored in valid RPC responses
UNKNOWN_COMMAND_PATTERN = re.compile(r'Unknown command:\s*\d+', re.IGNORECASE)

def is_error_response(response: str) -> bool:
    """
    Determine if a response is an actual error or a valid response.
    
    Args:
        response (str): The response string to check
        
    Returns:
        bool: True if the response is an error, False otherwise
    """
    if not response:
        logger.debug("Response is empty, not an error.")
        return False
        
    # First, check if any valid response patterns are present
    is_valid_response_present = False
    for pattern in VALID_RESPONSE_PATTERNS:
        if pattern.search(response):
            logger.debug(f"Response matches valid pattern '{pattern.pattern}'.")
            is_valid_response_present = True
            break
            
    # If a valid response is present, and the "Unknown command: 0" is also present,
    # we consider it a valid response as per user's clarification for RPC.
    if is_valid_response_present and UNKNOWN_COMMAND_PATTERN.search(response):
        logger.debug(f"Valid response pattern found and 'Unknown command: 0' detected, but it's considered valid for RPC. Identified as valid: {response[:100]}...")
        return False

    # If no valid response patterns are present, or if a valid response is present
    # but "Unknown command: 0" is not, then proceed to check for general errors.
    for pattern in BASE_ERROR_PATTERNS:
        if pattern.search(response):
            logger.debug(f"Response matches error pattern '{pattern.pattern}'. Identified as error: {response[:100]}...")
            return True
            
    # If no patterns match, it's not an error
    logger.debug(f"Response identified as non-error (no matching patterns): {response[:100]}...")
    return False