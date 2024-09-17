import uuid
from datetime import datetime
from typing import List, Optional, Union
from zoneinfo import ZoneInfo

from dateutil.parser import parse
from pydantic import BaseModel, Field, HttpUrl, field_validator
from traitlets import default


class RSSItem(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    link: HttpUrl
    creator: Optional[str] = Field(None)
    pub_date: datetime = Field()
    categories: List[str] = Field(default_factory=list)
    guid: str
    description: str
    outlet: str = Field(default="TechCrunch")
    processed: bool = Field(default=False)

    def model_dump(self, **kwargs):
        # Call the super().model_dump() to get the original dictionary
        data = super().model_dump(**kwargs)
        # Convert id, link, and pub_date to strings
        data['id'] = str(self.id)
        data['link'] = str(self.link)
        # Convert pub_date to ISO 8601 string
        data['pub_date'] = self.pub_date.isoformat()
        data['processed'] = int(self.processed)
        return data

    @field_validator('pub_date', mode='before')
    def parse_pub_date(cls, value: Union[str, datetime]) -> datetime:
        """
        Parse the pub_date field, supporting multiple date formats.

        Args:
            value (Union[str, datetime]): The date to parse.

        Returns:
            datetime: The parsed datetime object.

        Raises:
            ValueError: If the date string cannot be parsed.
        """
        if isinstance(value, datetime):
            return value.replace(tzinfo=ZoneInfo("UTC"))

        if isinstance(value, str):
            try:
                # Try parsing as RFC 2822 format
                dt = datetime.strptime(value, '%a, %d %b %Y %H:%M:%S %z')
            except ValueError:
                try:
                    # Try parsing as ISO 8601 format
                    dt = datetime.fromisoformat(value)
                except ValueError:
                    # Use dateutil's parser as a fallback
                    dt = parse(value)

            # Ensure timezone is set to UTC
            return dt.astimezone(ZoneInfo("UTC"))

        raise ValueError(f"Unsupported date format: {value}")
