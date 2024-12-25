from typing import TypedDict

Feat = list[str]
    
class Build(TypedDict):
    level: int
    feats: list[Feat]
    specials: list[str]
    proficiencies: dict[str, int]
