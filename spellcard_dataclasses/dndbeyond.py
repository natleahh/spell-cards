import itertools
from spellcard_dataclasses import common
from spellcard_structs import dndbeyond


class Build(common.CommonBuild):
    STRUCTURE = dndbeyond.Build
    
    @classmethod
    def from_json_data(cls, json_data):
        return cls._from_json_data(json_data, "data")

    @classmethod
    def from_json_id(cls, json_id: int):
        return cls._from_url(
            "data", 
            "https://character-service.dndbeyond.com/character/v5/character/{}", 
            (json_id,),
            )
    
    @property
    def all_actions(self):
        actions = itertools.chain(
            itertools.chain.from_iterable(classSpell.get("spells") for classSpell in self["classSpells"]),
            *filter(bool, self["actions"].values()),
            *filter(bool, self["spells"].values())
        )
        return [*actions]
    
    @property
    def all_action_names(self):
        return [action["name"] if "name" in action else action["definition"]["name"] for action in self.all_actions]
        