import logging
import re


def contains_markdown(text: str) -> bool:
    """
    Checks if the given text contains any Markdown formatting.

    Args:
        text (str): The input string to check for Markdown syntax.

    Returns:
        bool: True if Markdown formatting is found, False otherwise.
    """
    logger = logging.getLogger("AppLogger")
    logger.debug("Checking for Markdown in the provided text.")

    # Define regex patterns for various Markdown elements
    markdown_patterns = [
        r'^\s{0,3}(#{1,6})\s+',  # Headers: # Header, ## Header, etc.
        r'\*\*(.*?)\*\*',  # Bold: **bold**
        r'\*(.*?)\*',  # Italic: *italic*
        r'__(.*?)__',  # Bold: __bold__
        r'_(.*?)_',  # Italic: _italic_
        r'!\[.*?\]\(.*?\)',  # Images: ![alt](url)
        r'\[.*?\]\(.*?\)',  # Links: [text](url)
        r'`{1,3}[^`]+`{1,3}',  # Inline code: `code` or ```code```
        r'^\s{0,3}[-*+] ',  # Unordered lists: -, *, +
        r'^\s*\d+\.\s+',  # Ordered lists: 1., 2., etc.
        r'>\s+',  # Blockquotes: > quote
        r'^\s{0,3}#{3,}\s*$',  # Horizontal rules: ### or ---
        r'```[\s\S]*?```',  # Fenced code blocks: ```python ... ```
        r'~~(.*?)~~',  # Strikethrough: ~~text~~
    ]

    # Compile the patterns for better performance
    compiled_patterns = [re.compile(pattern, re.MULTILINE | re.DOTALL) for pattern in markdown_patterns]

    # Check each pattern
    for pattern in compiled_patterns:
        if pattern.search(text):
            logger.debug("Markdown pattern matched: %s", pattern.pattern)
            return True

    logger.debug("No Markdown patterns matched.")
    return False