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
    def all_spells(self):
        actions = itertools.chain(
            itertools.chain.from_iterable(classSpell.get("spells") for classSpell in self["classSpells"]),
            *filter(bool, self["spells"].values())
        )
        return [*actions]
    
    @staticmethod
    def get_name(action):
        return action.get("name") or action["definition"]["name"]
    
    @property
    def all_actions(self):
        return [*filter(bool, self["actions"].values())]
