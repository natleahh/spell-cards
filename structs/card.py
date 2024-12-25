from typing import Literal, TypedDict


ContentType = Literal["subtitle", "rule", "property", "text"]

class RPGCard(TypedDict):
    title: str
    count: str
    color: str
    title: str
    icon: str
    icon_back: str
    contents: list[str]
    tags: list[str]