

from typing import Literal, Optional, TypedDict

ActionSource = Literal["race", "class", "background", "item", "feat"]

class ActionDefinition(TypedDict):
    name: str

class Action(TypedDict):
    definition: Optional[ActionDefinition]
    name: Optional[str]

class ClassSpell(TypedDict):
    spells: list[Action]

ActionSummary = dict[ActionSource, Action]

class Build(TypedDict):
    actions: ActionSummary
    spells: ActionSummary
    classSpells: list[ClassSpell]