import re
from spellcard_dataclasses import common
from spellcard_structs import dnd5etools
import utils
from utils import static

SOURCES = ["PHB", "TCE", "XGE"]
    
class Spell(common.DBItemCommon):
    STRUCTURE = dnd5etools.Spell
    SOURCES = SOURCES
    DATA = utils.load_dnd_5e_spells(SOURCES)
    
    def get_school(self):
        try:
            return static.SCHOOL_MAPPING[self["school"]]
        except KeyError:
            raise KeyError(f"Abbreviated school {self['school']} in spell {self['name']} doesn't have mapped name.")
        
    
    def get_spell_level(self):
        match self["level"]:
            case 0:
                return "cantrip"
            case 1:
                return "1st level"
            case 2:
                return "2nd level"
            case 3:
                return "3rd level"
            case n if n in range(4, 10):
                return f"{n}th level"
            case _:
                raise ValueError(f"Unsupported spell level {self['level']}")
    
    def get_casting_time(self):
        return ", ".join(
            "{number} {unit}".format(**each)
            for each in self["time"]
        ) or None
        
    def get_range(self):
        match self["range"]:
            case None:
                return None
            case {"type": "special", **__}:
                return "special"
            case {"type": "point", **details}:
                match details["distance"]:
                    case {"type": value}:
                        return f"{value}"
                    case _:
                        return "{type} {amount}".format(**details["distance"])
            case _:
                raise ValueError(f"Unsupported range type: {self['range']['type']} for spell {self['name']}")
            
    
    def get_components(self):
        component_strs = []
        
        for component, details in self["components"].items():
            match details:
                case True:
                    component_strs.append(component.upper())
                    continue
                case {"text": details}:
                    pass
                case _:
                    pass
            component_strs.append(f"{component} ({details})")
            
        return ", ".join(component_strs) or None

    def get_duration(self):
        durations = []
        for duration in self["duration"]:
            template = "{amount} {type}"
            
            if duration["type"] != "timed":
                continue
            duration_details = duration["duration"]
            if duration_details.get("concentration") is True and "concentration" not in durations:
                durations.append("concentration")
            if duration_details.get("upTo") is True:
                template = "up to {}".format(template)
            if duration_details.get("ends"):
                end_terms = map("{}ed".format, duration_details["ends"])
                durations.append(f"until {utils.word_list(end_terms, join='or')}")
                
                
            durations.append(
                template.format(type=duration_details["type"], amount=duration_details["amount"])
            )
        return ", ".join(durations) or None
        
    
    def get_header_data(self):
        return {
            "Casting Time": self.get_casting_time(),
            "Range": self.get_range(),
            "Components": self.get_components(),
            "Duration": self.get_duration()
        }