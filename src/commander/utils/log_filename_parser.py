"""
Log Filename Parser - Utility for extracting IP addresses from log filenames
"""
import re
import logging


def extract_ip_from_filename(filename: str) -> str:
    """
    Extract IP address from log filename using pattern matching.
    
    Args:
        filename: Name of the log file
        
    Returns:
        Extracted IP address as string, or empty string if not found
    """
    if not filename:
        return ""
        
    # Pattern to match IP addresses in various log filename formats
    # Examples: AP01m_192-168-0-11_162.fbc, AL01_192-168-0-52_exe1_5irb_5orb.lis
    ip_patterns = [
        r'_(\d{1,3})-(\d{1,3})-(\d{1,3})-(\d{1,3})_',  # Dashed format: 192-168-0-11
        r'_(\d{1,3})_(\d{1,3})_(\d{1,3})_(\d{1,3})_',   # Underscore format: 192_168_0_11
        r'_(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})_' # Dot format: 192.168.0.11
    ]
    
    for pattern in ip_patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                # Convert to standard IP format
                ip_parts = [int(part) for part in match.groups()]
                # Validate IP ranges
                if all(0 <= part <= 255 for part in ip_parts):
                    return ".".join(str(part) for part in ip_parts)
            except (ValueError, IndexError):
                continue
                
    logging.debug(f"No IP address found in filename: {filename}")
    return ""


def is_valid_ip(ip: str) -> bool:
    """
    Validate if a string is a valid IP address.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        True if valid IP address, False otherwise
    """
    if not ip:
        return False
        
    parts = ip.split('.')
    if len(parts) != 4:
        return False
        
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False