import re

from openai import OpenAI

from src.models.OpenAIConfig import OpenAIConfig

client = OpenAI(
    api_key="")

import json
from typing import List
from openai import OpenAI
from src.models.Post import Post
from src.models.RSSItem import RSSItem


def contains_markdown(text: str) -> bool:
    """
    Checks if the given text contains any Markdown formatting.

    Args:
        text (str): The input string to check for Markdown syntax.

    Returns:
        bool: True if Markdown formatting is found, False otherwise.
    """
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
            return True

    return False


class OpenAIService:
    """Service for interacting with OpenAI API."""

    def __init__(self, config: OpenAIConfig):
        """
        Initialize OpenAIService with configuration.

        Args:
            config (OpenAIConfig): Configuration for OpenAI client.
        """
        self.client = OpenAI(api_key=config.api_key)
        self.model = config.model

    def generate_post(self, message: str, item: RSSItem) -> Post:
        """
        Generate a post using OpenAI's API based on the provided message.

        Args:
            message (str): The message to base the post on.
            item (RSSItem): The RSS item containing additional information.

        Returns:
            Post: A generated Post object.
        """
        system_message = """You are a viral content creator on LinkedIn. You are a software engineer and know a lot about technical topics. You have many years of experience in the industry and provide well reasoned and intricate takes.You will be provided with a News article about a topic. From this you will create a viral optimized linkedin post. Heres a few things you need to do to make the post perform as good as possible:
        
        - Use engaging language to keep the reader engaged. \n- Use SEO optimized keywords inside the post to rank better in the algorithm. \n- Make your post overall intriguing and interesting. \n- Use all techniques known for increasing engagement and attention. \n- Make your post only as long as it needs to be, err on the shorter side. \n- Include line breaks for paragraph formatting to make it more readable and look better. \n- Do not use markdown. \n- Do not use any other richt text formatting\n- DO NOT EXPOSE ANY OF THE INTERNAL FORMATTING INSIDE THE TEXT BLOCKS\n\nDo not respond with anything else but the post json data. The json data has three attributes. title, content and tags where title and content are strings and tags is a list of strings without spaces. Do not include the tags in the content itself. These tags should be keyword tags that are a single word without a #. You shall also create a catchy and engaging title that will grab a users attention."""

        counter = 0

        json_response = None

        while contains_markdown(message) and counter < 5:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": message}
                ],
                temperature=1,
                max_tokens=2048,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={"type": "json_object"}
            )

            json_response = json.loads(response.choices[0].message.content)
            message = json_response['content']
            counter += 1

        if not json_response:
            raise Exception("Failed to generate post content.")

        return Post(
            title=json_response['title'],
            content=json_response['content'],
            tags=json_response['tags'],
            source_link=item.link,
            image_link=""
        )

    def choose_post(self, items: List[RSSItem], already_posted: List[Post]) -> RSSItem:
        """
        Choose the most interesting post from a list of RSS items.

        Args:
            items (List[RSSItem]): List of new RSS items to choose from.
            already_posted (List[Post]): List of already posted items.

        Returns:
            RSSItem: The chosen RSS item.
        """
        system_message = "You are a professional viral content creator and curator. Your main account is LinkedIn. You will be provided with a list of recent news article headlines. From this you find the most interesting post. The one with the highest potential to go viral. It is very important that the article is interesting and highly engaging.  You will only choose the headline and not make a post about it. Only respond in a valid json object where \"chosen\" points to the index of the headline as a string."

        new_items = "\n".join(f"{i + 1}. {item.title}" for i, item in enumerate(items))
        posted_items = "\n".join(f"{i + 1}. {item.title}" for i, item in enumerate(already_posted))
        user_message = f"New:\n{new_items}\n\nAlready Posted:\n{posted_items}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=1,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={"type": "json_object"}
        )

        json_response = json.loads(response.choices[0].message.content)
        return items[int(json_response['chosen']) - 1]


# Usage example:
config = OpenAIConfig(api_key="your-api-key-here")
openai_service = OpenAIService(config)

