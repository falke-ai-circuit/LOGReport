import logging

# Test logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug.log')
    ]
)

# Test debug messages
logger = logging.getLogger(__name__)
logger.debug("This is a test debug message")
logger.info("This is a test info message")
logger.warning("This is a test warning message")

print("Logging test complete. Check debug.log for output.")