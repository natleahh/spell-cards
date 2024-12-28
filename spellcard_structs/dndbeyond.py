

from typing import Literal, TypedDict

ActionSource = Literal["race", "class", "background", "item", "feat"]

class Action(TypedDict):
    name: dict
    limitedUse: dict
    desctiption: str
    snipped: str


class Spell(Action):
    pass

ActionSummary = dict[ActionSource, Action]

SpellSummary = dict[ActionSource, Spell]

class Build(TypedDict):
    actions: ActionSummary
    spells: SpellSummary