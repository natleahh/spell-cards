from typing import Literal, Optional, TypedDict


       
class Activity(TypedDict):
    number: Optional[int]
    unit: Literal["free", "action", "reaction", "bonus action"]

class Action(TypedDict):
    name: str
    source: str
    traits: list[str]
    activity: Activity = None
    trigger: Optional[str]
    requirements: Optional[str] = None
    entries: list[str | dict] 

class Feat(TypedDict):
    name: str
    source: str
    traits: list[str]
    entries: list[str | dict]
    activity: Optional[Activity] = None
    requirements: Optional[str]
    