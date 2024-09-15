from openai import OpenAI

client = OpenAI(
    api_key="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")


class OpenAIService:

    @staticmethod
    def generate_post(message: str) -> str:
        """Generates a post using OpenAI's API based on the provided message."""
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a viral content creator on LinkedIn. You are a software engineer and know a lot about technical topics. You will be provided with a News article about a topic. From this you will create a viral optimized post. Use engaging language to keep the reader engaged. Use SEO optimized keywords inside the post to rank better in the algorithm. Make your post overall intriguing and interesting. You should use all techniques known for increasing engagement and attention. Make your post only as long as it needs to be, err on the shorter side. Do not address other users directly. Do not respond with anything else but the post. Include the source link before the tags."
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            temperature=1,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response['choices'][0]['message']['content']
