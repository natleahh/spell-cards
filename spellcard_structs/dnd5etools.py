from typing import Literal, Optional, TypedDict

from utils import static

class Spell(TypedDict):
    name: str
    source: str
    level: str
    school: Literal["C", "A", "D", "E", "V", "I", "N", "T"]
    range: dict
    components: dict[Literal["v", "s", "m"], bool | str]
    entries: list
    entriesHigherLevels: list

class Monster(TypedDict):
    name: str
    spellcasting: Optional[list[dict]]