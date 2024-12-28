from typing import Literal, TypedDict

class Spell(TypedDict):
    name: str
    source: str
    level: str
    school: Literal["V"]
    range: dict
    components: dict[Literal["v", "s", "m"], bool]
    entries: list
    entriesHigherLevels: list
    
    