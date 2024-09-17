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

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are a viral content creator on LinkedIn. You are a software engineer and know a lot about technical topics. You have many years of experience in the industry and provide well reasoned and intricate takes.\n\nYou will be provided with a News article about a topic. From this you will create a viral optimized linkedin post. Heres a few things you need to do to make the post perform as good as possible:\n\n- Use engaging language to keep the reader engaged. \n- Use SEO optimized keywords inside the post to rank better in the algorithm. \n- Make your post overall intriguing and interesting. \n- Use all techniques known for increasing engagement and attention. \n- Make your post only as long as it needs to be, err on the shorter side. \n- Include line breaks for paragraph formatting to make it more readable and look better. \n- Do not use markdown. \n- Do not use any other richt text formatting\n- DO NOT EXPOSE ANY OF THE INTERNAL FORMATTING INSIDE THE TEXT BLOCKS\n\nDo not respond with anything else but the post json data. The json data has three attributes. title, content and tags where title and content are strings and tags is a list of strings without spaces. Do not include the tags in the content itself. These tags should be keyword tags that are a single word without a #. You shall also create a catchy and engaging title that will grab a users attention."
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
    def choose_post(items: List[RSSItem], already_posted: List[Post]) -> RSSItem:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are a professional viral content creator and curator. Your main account is LinkedIn. You will be provided with a list of recent news article headlines. From this you find the most interesting post. The one with the highest potential to go viral. It is very important that the article is interesting and highly engaging.  You will only choose the headline and not make a post about it. Only respond in a valid json object where \"chosen\" points to the index of the headline as a string."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "New:\n{}\n\nAlready Posted:\n{}".format(
                                "\n".join("{0}. {1}".format(i+1, item.title) for i, item in enumerate(items)),
                                "\n".join("{0}. {1}".format(i+1, item.title) for i, item in enumerate(already_posted))
                            )
                        }
                    ]
                }
            ],
            temperature=1,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={
                "type": "json_object"
            }
        )
        json_response = json.loads(response.choices[0].message.content)
        return items[int(json_response['chosen'])-1]