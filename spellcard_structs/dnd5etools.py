from typing import Literal, Optional, TypedDict

from utils import static

class Dnd5eToolsItem(TypedDict):
    name: str
    source: str
    entries: str

class Spell(Dnd5eToolsItem):
    level: str
    school: Literal["C", "A", "D", "E", "V", "I", "N", "T"]
    range: dict
    components: dict[Literal["v", "s", "m"], bool | str]
    entriesHigherLevels: list

class Monster(Dnd5eToolsItem):
    spellcasting: Optional[list[dict]]
    
class MagicItem(Dnd5eToolsItem):
    baseItem: Optional[str]
    reqAttube: bool = False