from pydantic import BaseModel, HttpUrl


class Post(BaseModel):
    content: str
    source_link: HttpUrl