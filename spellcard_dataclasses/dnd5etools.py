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
        return static.SCHOOL_MAPPING[self["school"]]
    
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