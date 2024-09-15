import uuid
from typing import List, Optional
from datetime import datetime
import requests
import boto3
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field, HttpUrl, validator, field_validator
import html2text
import openai

class RSSItem(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    link: HttpUrl
    creator: Optional[str] = Field(None)
    pub_date: datetime = Field(alias='pubDate')
    categories: List[str] = Field(default_factory=list, alias='category')
    guid: str
    description: str
    outlet:str="TechCrunch"

    def model_dump(self, **kwargs):
        # Call the super().model_dump() to get the original dictionary
        data = super().model_dump(**kwargs)
        # Convert id, link, and pub_date to strings
        data['id'] = str(self.id)
        data['link'] = str(self.link)
        # Convert pub_date to ISO 8601 string
        data['pub_date'] = self.pub_date.isoformat()
        return data

    @field_validator('pub_date', mode='before')
    def parse_pub_date(cls, value):
        return datetime.strptime(value, '%a, %d %b %Y %H:%M:%S %z')