from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict


def _datetime_to_utc_str(dt: datetime) -> str:
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


class AppModel(BaseModel):

    model_config = ConfigDict(
        json_encoders={datetime: _datetime_to_utc_str},
        populate_by_name=True,
        from_attributes=True,
    )
