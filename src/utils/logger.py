import logging
import sys

# Optional: Import colorama for cross-platform color support
try:
    import colorama
    colorama.init()
except ImportError:
    colorama = None

# Define ANSI color codes
class LogColors:
    RESET = "\033[0m"
    GRAY = "\033[90m"
    CYAN = "\033[96m"     # DEBUG
    BLUE = "\033[94m"     # INFO
    YELLOW = "\033[93m"   # WARNING
    RED = "\033[91m"      # ERROR
    MAGENTA = "\033[95m"  # CRITICAL

class ColorColumnFormatter(logging.Formatter):
    def format(self, record):
        # Format the timestamp
        time_str = self.formatTime(record, '%Y-%m-%d %H:%M:%S')
        message = record.getMessage()
        level = record.levelname
        filename = record.filename  # Get the filename

        # Optional: Get the function name or line number
        # function = record.funcName
        # lineno = record.lineno

        if level == 'ERROR':
            # Entire line in red
            color = LogColors.RED
            formatted = f"{color}{time_str:<20} | {level:<8} | {filename:<20} | {message:<50}{LogColors.RESET}"
        elif level == 'CRITICAL':
            # Entire line in magenta
            color = LogColors.MAGENTA
            formatted = f"{color}{time_str:<20} | {level:<8} | {filename:<20} | {message:<50}{LogColors.RESET}"
        else:
            # Different colors for log levels
            level_colors = {
                "DEBUG": LogColors.CYAN,
                "INFO": LogColors.BLUE,
                "WARNING": LogColors.YELLOW,
            }
            level_color = level_colors.get(level, LogColors.GRAY)
            time_colored = f"{LogColors.GRAY}{time_str:<20}{LogColors.RESET}"
            level_colored = f"{level_color}{level:<8}{LogColors.RESET}"
            filename_colored = f"{LogColors.GRAY}{filename:<20}{LogColors.RESET}"
            message_colored = f"{LogColors.GRAY}{message:<50}{LogColors.RESET}"
            formatted = f"{time_colored} | {level_colored} | {filename_colored} | {message_colored}"

        return formatted

def setup_logger(name="AppLogger", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create Stream Handler (console)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(ColorColumnFormatter())

    # Avoid adding multiple handlers if the logger already has handlers
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


# Example Usage
if __name__ == "__main__":
    logger = setup_logger()

    # Log messages of various levels
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")