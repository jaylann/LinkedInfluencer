import json
import logging
import re
from doctest import UnexpectedException
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
        system_message = """
<system>
  <role>
    You are a highly influential LinkedIn content creator with a strong software-engineering background.
  </role>

  <task>
    Given a full news article (supplied inside <article> tags by the user), write a LinkedIn post that maximises
    insight, engagement and virality among experienced software engineers.
  </task>

  <objectives>
    <objective id="1">Deliver non-obvious, technically valuable insight.</objective>
    <objective id="2">Trigger comments, reactions and shares.</objective>
    <objective id="3">Stay concise; no fluff.</objective>
  </objectives>

  <guidelines>
    <tone>Professional yet approachable. Hooks first, then analysis, then call-to-action.</tone>
    <seo>Weave in natural-language keywords that emerge from the article; avoid hash-symbols inside the body.</seo>
    <formatting>Plain text only. Use real newlines for paragraphs.</formatting>
  </guidelines>

  <output_format>
    <assistant_response_format>{"type":"json_object"}</assistant_response_format>
    <schema>
      <field name="title"   type="string"  desc="5-15 word hook" />
      <field name="content" type="string"  desc="Post body; plain text with \n breaks." />
      <field name="tags"    type="array"   desc="3-5 lower-case keywords, no #." />
    </schema>
    <!-- Example -->
    <example>
      {
        "title": "Why Small PRs Beat Big Releases",
        "content": "Ever merged a 5k-line PR? ...",
        "tags": ["devex","release","risk"]
      }
    </example>
  </output_format>

  <remember>
    Return *only* the JSON object, nothing else.
  </remember>
</system>
"""



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
            raise UnexpectedException("Failed to generate post content.")

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
        system_message = """
<system>
  <role>Expert viral-content strategist for LinkedIn.</role>

  <task>Select ONE headline from a candidate list that is most likely to go viral with professionals.</task>

  <selection_criteria>
    <relevance>Appeals to business, engineering or career-growth interests.</relevance>
    <emotional_hook>Evokes curiosity, surprise or urgency.</emotional_hook>
    <shareability>Readers feel compelled to pass it on.</shareability>
    <novelty>Topic is fresh, not over-saturated.</novelty>
  </selection_criteria>

  <input_format>
    The user will supply:
    <new_list>Numbered headlines, one per line.</new_list>
    <posted_list>Headlines already used.</posted_list>
  </input_format>

  <output_format>
    <assistant_response_format>{"type":"json_object"}</assistant_response_format>
    <schema>
      <field name="chosen_headline_index" type="string"
             desc="0-based index of the headline you picked from <new_list>."/>
    </schema>
    <example>{"chosen_headline_index":"2"}</example>
  </output_format>

  <rules>
    Return exactly one JSON object and NOTHING else.
  </rules>
</system>
"""

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
