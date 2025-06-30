import logging
import traceback
import datetime

# Logger shared across bot
logger = logging.getLogger("nova")

def log_error(source: str, error: Exception):
    """Log a structured error with traceback."""
    logger.error(f"[{source}] {str(error)}")
    tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    logger.debug(tb)

def user_error(message: str) -> str:
    """Return a clean user-facing error message."""
    return f"⚠️ {message}"

def timestamp() -> str:
    """Return current UTC time string."""
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

def log_error(context: str, e: Exception, include_trace: bool = False):
    msg = f"❌ {context}: {e}"
    if include_trace:
        import traceback
        msg += "\n" + traceback.format_exc()
    logger.error(msg)
