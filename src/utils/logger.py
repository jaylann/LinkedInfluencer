import logging
import sys

try:
    import colorama
    colorama.init()
except ImportError:
    colorama = None

class LogColors:
    RESET = "\033[0m"
    GRAY = "\033[90m"
    CYAN = "\033[96m"    # DEBUG
    BLUE = "\033[94m"    # INFO
    YELLOW = "\033[93m"  # WARNING
    RED = "\033[91m"     # ERROR
    MAGENTA = "\033[95m" # CRITICAL

class ColorColumnFormatter(logging.Formatter):
    def format(self, record):
        time_str = self.formatTime(record, '%Y-%m-%d %H:%M:%S')
        filename = f"{record.filename}:{record.lineno}"  # File name and line number
        function = record.funcName                      # Function name
        message = record.getMessage()
        level = record.levelname

        if level == 'ERROR':
            # Entire line in red
            color = LogColors.RED
            formatted = f"{color}{time_str:<20} | {filename:<30} | {function:<20} | {level:<8} | {message:<50}{LogColors.RESET}"
        elif level == 'CRITICAL':
            # Entire line in magenta
            color = LogColors.MAGENTA
            formatted = f"{color}{time_str:<20} | {filename:<30} | {function:<20} | {level:<8} | {message:<50}{LogColors.RESET}"
        else:
            # Different colors for log levels
            level_colors = {
                "DEBUG": LogColors.CYAN,
                "INFO": LogColors.BLUE,
                "WARNING": LogColors.YELLOW,
            }
            level_color = level_colors.get(level, LogColors.GRAY)
            time_colored = f"{LogColors.GRAY}{time_str:<20}{LogColors.RESET}"
            filename_colored = f"{LogColors.GRAY}{filename:<30}{LogColors.RESET}"
            function_colored = f"{LogColors.GRAY}{function:<20}{LogColors.RESET}"
            level_colored = f"{level_color}{level:<8}{LogColors.RESET}"
            message_colored = f"{LogColors.GRAY}{message:<50}{LogColors.RESET}"
            formatted = f"{time_colored} | {filename_colored} | {function_colored} | {level_colored} | {message_colored}"

        return formatted

def setup_logger(name="AppLogger", level=logging.DEBUG):
    logger = logging.getLogger(name)

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(ColorColumnFormatter())

    if not logger.handlers:
        logger.addHandler(handler)

    logging.basicConfig(level=logging.DEBUG, handlers=[handler])
    return logger
