import json
import random
from typing import List

from openai import OpenAI

from src.models.Post import Post
from src.models.RSSItem import RSSItem

client = OpenAI(
    api_key="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")


class OpenAIService:

    @staticmethod
    def generate_post(message: str, item: RSSItem) -> Post:
        """Generates a post using OpenAI's API based on the provided message."""
        from openai import OpenAI
        client = OpenAI(api_key="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")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are a viral content creator on LinkedIn. You are a software engineer and know a lot about technical topics. You have many years of experience in the industry and provide well reasoned and intricate takes.\n\nYou will be provided with a News article about a topic. From this you will create a viral optimized linkedin post. Heres a few things you need to do to make the post perform as good as possible:\n\n- Use engaging language to keep the reader engaged. \n- Use SEO optimized keywords inside the post to rank better in the algorithm. \n- Make your post overall intriguing and interesting. \n- Use all techniques known for increasing engagement and attention. \n- Make your post only as long as it needs to be, err on the shorter side. \n- Include line breaks for paragraph formatting to make it more readable and look better. \n- Do not use markdown. \n- Do not use any other richt text formatting\n- DO NOT EXPOSE ANY OF THE INTERNAL FORMATTING INSIDE THE TEXT BLOCKS\n\nDo not respond with anything else but the post json data. The json data has three attributes. title, content and tags where title and content are strings and tags is a list of strings without spaces. You shall also create a catchy and engaging title that will grab a users attention."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{message}"
                        }
                    ]
                }
            ],
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={
                "type": "json_object"
            }
        )
        json_response = json.loads(response.choices[0].message.content)
        return Post(title=json_response['title'],
                    content=json_response['content'],
                    tags=json_response['tags'],
                    source_link=item.link)

    @staticmethod
    def choose_post(items: List[RSSItem]) -> RSSItem:
        """Chooses the best RSSItem to create a post from."""
        # For now, just choose the first item
        return random.choice(items)