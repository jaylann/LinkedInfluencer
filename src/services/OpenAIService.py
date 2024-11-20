import json
import logging
import re
from typing import List

from openai import OpenAI

from src.models.OpenAIConfig import OpenAIConfig
from src.models.Post import Post
from src.models.RSSItem import RSSItem
from src.utils.TextUtils import contains_markdown


class OpenAIService:
    """Service for interacting with OpenAI API."""

    def __init__(self, config: OpenAIConfig):
        """
        Initialize OpenAIService with configuration.

        Args:
            config (OpenAIConfig): Configuration for OpenAI client.
        """
        self.logger = logging.getLogger("AppLogger")
        self.logger.info("Initializing OpenAIService with model: %s", config.model)
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
        self.logger.info("Starting post generation for RSS item: %s", item.title)
        system_message = """You are a viral content creator on LinkedIn. You are a software engineer and know a lot about technical topics. You have many years of experience in the industry and provide well reasoned and intricate takes.You will be provided with a News article about a topic. From this you will create a viral optimized linkedin post. Heres a few things you need to do to make the post perform as good as possible:
        
        - Use engaging language to keep the reader engaged. \n- Use SEO optimized keywords inside the post to rank better in the algorithm. \n- Make your post overall intriguing and interesting. \n- Use all techniques known for increasing engagement and attention. \n- Make your post only as long as it needs to be, err on the shorter side. \n- Include line breaks for paragraph formatting to make it more readable and look better. \n- Do not use markdown. \n- Do not use any other richt text formatting\n- DO NOT EXPOSE ANY OF THE INTERNAL FORMATTING INSIDE THE TEXT BLOCKS\n\nDo not respond with anything else but the post json data. The json data has three attributes. title, content and tags where title and content are strings and tags is a list of strings without spaces. Do not include the tags in the content itself. These tags should be keyword tags that are a single word without a #. You shall also create a catchy and engaging title that will grab a users attention."""

        counter = 0
        max_attempts = 5
        json_response = None

        while contains_markdown(message) and counter < max_attempts:
            self.logger.debug("Attempt %d to generate post without Markdown.", counter + 1)
            try:
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
                self.logger.debug("Received response from OpenAI API.")
                json_response = json.loads(response.choices[0].message.content)
                self.logger.debug("Parsed JSON response: %s", json_response)
                message = json_response.get('content', '')
                counter += 1
            except json.JSONDecodeError as e:
                self.logger.error("JSON decoding failed: %s", e)
                raise
            except Exception as e:
                self.logger.error("Error during OpenAI API call: %s", e)
                raise

        if not json_response:
            self.logger.error("Failed to generate post content after %d attempts.", max_attempts)
            raise Exception("Failed to generate post content.")

        post = Post(
            title=json_response['title'],
            content=json_response['content'],
            tags=json_response['tags'],
            source_link=item.link,
            image_link=""
        )
        self.logger.info("Successfully generated post: %s", post.title)
        return post

    def choose_post(self, items: List[RSSItem], already_posted: List[Post]) -> RSSItem:
        """
        Choose the most interesting post from a list of RSS items.

        Args:
            items (List[RSSItem]): List of new RSS items to choose from.
            already_posted (List[Post]): List of already posted items.

        Returns:
            RSSItem: The chosen RSS item.
        """
        self.logger.info("Choosing a post from %d new items.", len(items))
        system_message = "You are a professional viral content creator and curator. Your main account is LinkedIn. You will be provided with a list of recent news article headlines. From this you find the most interesting post. The one with the highest potential to go viral. It is very important that the article is interesting and highly engaging.  You will only choose the headline and not make a post about it. Only respond in a valid json object where \"chosen\" points to the index of the headline as a string."

        new_items = "\n".join(f"{i + 1}. {item.title}" for i, item in enumerate(items))
        posted_items = "\n".join(f"{i + 1}. {item.title}" for i, item in enumerate(already_posted))
        user_message = f"New:\n{new_items}\n\nAlready Posted:\n{posted_items}"

        try:
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
            self.logger.debug("Received response from OpenAI API for choosing post.")
            json_response = json.loads(response.choices[0].message.content)
            chosen_index = int(json_response['chosen']) - 1
            if not (0 <= chosen_index < len(items)):
                self.logger.error("Chosen index %d is out of bounds.", chosen_index)
                raise IndexError("Chosen index is out of bounds.")
            chosen_item = items[chosen_index]
            self.logger.info("Chosen post: %s", chosen_item.title)
            return chosen_item
        except json.JSONDecodeError as e:
            self.logger.error("JSON decoding failed: %s", e)
            raise
        except (KeyError, ValueError, IndexError) as e:
            self.logger.error("Invalid response format or index error: %s", e)
            raise
        except Exception as e:
            self.logger.error("Error during OpenAI API call: %s", e)
            raise
