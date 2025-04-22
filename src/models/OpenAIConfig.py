import os

from pydantic import Field, BaseModel


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI client."""
    api_key: str = Field(os.getenv("OPENAI_API_KEY"), description="OpenAI API key")
    model: str = Field("gpt-4.1", description="OpenAI model to use")
