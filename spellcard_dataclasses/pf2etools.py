import itertools
import re
from typing import Optional, Self
from spellcard_dataclasses import common
from spellcard_structs import pf2etools
from utils import sources, static


LEGACY_CHANGES = [
    (r"(.*)Tripkee(.*)", "\g<1>Grippli\g<2>"),
    (r"Stunning Blows", "Stunning Fist")
]

def legacy_compat(name: str):
    for pattern, sub in LEGACY_CHANGES:
        if re.match(pattern, name) is None:
            continue
        return re.sub(pattern, sub, name)
    return name

class LegacySupport:
    
    @staticmethod
    def legacy_compatbility(name):
        return legacy_compat(name)

class Action(LegacySupport, common.DBItemCommon):
    
    STRUCTURE = pf2etools.Action
    SOURCES = static.SOURCES
    DATA = sources.ACTION_DATA
    
    def get_source_index(self):
        try:
            return static.SOURCES.index(self["source"])
        except ValueError:
            return 255
    
    def get_name(self):
        return self["name"]
    
    @classmethod
    def sort_key(cls, inst):
        return cls.get_name(inst), cls.get_source_index(inst)
    
    @classmethod
    def get_unique(cls, actions: list[Self]):
        by_name = {
            k: list(v)
            for k, v 
            in itertools.groupby(
                sorted(actions, key=Action.sort_key), key=Action.get_name
            )
        }
        return [actions[0] for actions in by_name.values()]


class Feat(LegacySupport, common.DBItemCommon):
    
    STRUCTURE = pf2etools.Feat
    SOURCES = static.SOURCES
    DATA = sources.FEAT_DATA
        
    def get_all_actions(self):
 
        all_actions = []
        
        if self is None:
            return all_actions
        
        if self["activity"] is not None:
            all_actions.append(Action.from_raw_dict(self))
        
        for entry in self["entries"]:
            if isinstance(entry, str):
                all_actions.extend(
                    Action.from_name(action_name, source or None)
                    for action_name, _, source in
                    re.findall(r"@action ([^\|}]+)(\|(\w+))?", entry)
                )
                all_actions.append(self)
            elif isinstance(entry, dict) and entry.get("activity") is not None:
                all_actions.append(Action.from_raw_dict(entry))

        return Action.get_unique(all_actions)