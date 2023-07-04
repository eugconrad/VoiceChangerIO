
from pydantic import BaseModel, ConfigDict
from selenium.webdriver.remote.webelement import WebElement


class VoiceEffect(BaseModel):  # type: ignore[misc]
    id: int
    title: str
    element: WebElement

    model_config = ConfigDict(arbitrary_types_allowed=True)
