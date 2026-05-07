import logging
import logging.handlers
import os
from datetime import datetime

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create logger for scheduler
scheduler_logger = logging.getLogger("scheduler")
scheduler_logger.setLevel(logging.DEBUG)

# Create file handler for scheduler logs
log_file = os.path.join(LOG_DIR, f"scheduler_{datetime.now().strftime('%Y%m%d')}.log")
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
scheduler_logger.addHandler(file_handler)
scheduler_logger.addHandler(console_handler)


# Create logger for decision events
decision_logger = logging.getLogger("decision")
decision_logger.setLevel(logging.DEBUG)

decision_log_file = os.path.join(LOG_DIR, f"decision_{datetime.now().strftime('%Y%m%d')}.log")
decision_file_handler = logging.handlers.RotatingFileHandler(
    decision_log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5
)
decision_file_handler.setLevel(logging.DEBUG)
decision_file_handler.setFormatter(formatter)

decision_logger.addHandler(decision_file_handler)
decision_logger.addHandler(console_handler)


# Create logger for audit events
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.DEBUG)

audit_log_file = os.path.join(LOG_DIR, f"audit_{datetime.now().strftime('%Y%m%d')}.log")
audit_file_handler = logging.handlers.RotatingFileHandler(
    audit_log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5
)
audit_file_handler.setLevel(logging.DEBUG)
audit_file_handler.setFormatter(formatter)

audit_logger.addHandler(audit_file_handler)
audit_logger.addHandler(console_handler)


def get_scheduler_logger():
    """Get scheduler logger instance"""
    return scheduler_logger


def get_decision_logger():
    """Get decision logger instance"""
    return decision_logger


def get_audit_logger():
    """Get audit logger instance"""
    return audit_logger
