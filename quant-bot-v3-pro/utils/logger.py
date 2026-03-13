import logging
from config import LOG_FILE, LOG_LEVEL

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

# File handler
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(LOG_LEVEL)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)
