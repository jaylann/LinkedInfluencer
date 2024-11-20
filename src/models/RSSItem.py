import uuid
from datetime import datetime
from typing import List, Optional, Union
from zoneinfo import ZoneInfo

from dateutil.parser import parse
from pydantic import BaseModel, Field, HttpUrl, field_validator

class RSSItem(BaseModel):
    """
    Represents an RSS feed item with various attributes.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    link: HttpUrl
    creator: Optional[str] = None
    pub_date: datetime
    categories: List[str] = Field(default_factory=list)
    guid: str
    description: str
    outlet: str = "TechCrunch" # Just in case
    processed: bool = False

    def model_dump(self, **kwargs) -> dict:
        """
        Dumps the model to a dictionary with custom formatting for certain fields.

        Returns:
            dict: A dictionary representation of the RSSItem with formatted fields.
        """
        data = super().model_dump(**kwargs)
        data.update({
            'id': str(self.id),
            'link': str(self.link),
            'pub_date': self.pub_date.isoformat(),
            'processed': int(self.processed)
        })
        return data

    @field_validator('pub_date', mode='before')
    @classmethod
    def parse_pub_date(cls, value: Union[str, datetime]) -> datetime:
        """
        Parses the pub_date field, supporting multiple date formats.

        Args:
            value: The date to parse, either as a string or datetime object.

        Returns:
            A datetime object in UTC timezone.

        Raises:
            ValueError: If the date string cannot be parsed.
        """
        if isinstance(value, datetime):
            return value.astimezone(ZoneInfo("UTC"))

        if isinstance(value, str):
            for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z'):
                try:
                    return datetime.strptime(value, fmt).astimezone(ZoneInfo("UTC"))
                except ValueError:
                    continue

            try:
                return parse(value).astimezone(ZoneInfo("UTC"))
            except ValueError:
                pass

        raise ValueError(f"Unsupported date format: {value}")