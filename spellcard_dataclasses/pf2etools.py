import abc
import itertools
import logging
import re
from typing import Optional, Self
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

class PF2EAbstract(abc.ABC):

	@classmethod
	def from_raw_dict(cls, data: dict):
		filtered_data = {
			k: v.from_raw_dict() if "from_raw_dict" in type(v).__dict__ else v
			for k, v 
			in data.items() if k in cls.__annotations__
		}
		
		return cls(filtered_data)
		
	@classmethod
	def from_name(cls, name: str, source: Optional[str], data_source: pd.DataFrame): # type: ignore
		name = legacy_compat(name)
		try: 
			query = data_source.loc[name]
		except:
			logging.error(f"No record called {name} in database.")
			return
		if query.size > 1:
			try:
				query = query.loc[source].head(1)
			except:
				query = query.sort_values(
					by="source",
					key=lambda col: col.map(lambda v: 255 if v not in static.SOURCES else static.SOURCES.index(v))
				).head(1)
				source = query.index.to_list()[0][0]
		raw_dict = query.replace(float("nan"), None).squeeze().to_dict()
		return cls.from_raw_dict(data={"name": name, "source": raw_dict.get("source") or source, **raw_dict})
	
class Action(pf2etools.Action, PF2EAbstract):
    
    @classmethod
    def from_name(cls, name: str, source: Optional[str] = None):
        return super(constructor=cls, name=name, source=source, data_source=sources.ACTION_DATA)
    
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


class Feat(pf2etools.Feat, PF2EAbstract):
    
    @classmethod
    def from_name(cls, name: str, source: Optional[str] = None):
        return super().from_name(name=name, source=source, data_source=sources.FEAT_DATA)
    
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