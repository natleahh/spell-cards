
from itertools import starmap
import itertools
import re
from formatting import CardData


class PFCardData(CardData):

    @classmethod
    def handle_entry(cls, entry):
        try:
            return super().handle_entry(entry)
        except ValueError:
            pass
        except:
            cls._raise_entry(entry)
            
        match entry["type"]:
            case "successDegree":
                return [*starmap("property | {} | {}".format, entry["entries"].items())]
            case "ability":
                return cls.to_ability(entry)
            case "affliction":
                return cls.to_affiction(entry)
            case "lvlEffect":
                return [
                    f"property | {e['range']} | {e['entry']}"
                    for e in entry['entries']
                ]
            case "pf2-options":
                return [
                    [f"property | {item['name']}", *map(cls.handle_entry, item["entries"])]
                    for item in [entry["items"]]
                ]
        
        cls._raise_entry(entry)
    
    @staticmethod
    def camel_to_words(string: str):
        return '_'.join(
            re.sub('([A-Z][a-z]+)', r' \1',
            re.sub('([A-Z]+)', r' \1',
            string.replace('-', ' '))).split()).lower()
    
    @staticmethod
    def get_sub_paragraph_details(entry, keys):
        return " ".join(
            f"<b>{PFCardData.camel_to_words(key)}:</b> {entry[key]}"
            for key  in keys
        )
    
    @classmethod
    def to_affiction(cls, entry):
        base = f"property | {entry['name']} | ({', '.join(entry['traits'])})"
        details = cls.get_sub_paragraph_details(entry, ["level", "maxDuration"])
        return [
            f"{base} {details} {entry.get('note')}",
            *(
                f"bullet | Stage {e['stage']}: {e['entry']} ({e['duration']})"
                for e in entry["stages"]
            )
        ]
    
    @classmethod
    def to_ability(cls, entry):
        match entry["activity"]:
            case {"unit": "reaction", **__}:
                activity = "R"
                header = f"<b>Trigger:</b> {entry['trigger']}. <b>Effect:</b>: "
            case {"unit": "action", "number": n}:
                activity = f"{n}"
                header = "<b>Effect:</b>: "
            case _:
                raise ValueError()
        body = " ".join(entry["entries"])
        return [
            f"p2e_activity | {entry['name']} | {activity} | ({', '.join(entry.get('traits', []))}) {header + body}"
        ]
    
    @classmethod
    def to_level_effect(cls, entry):
        return [
            f"property | {e['range']} | {e['entry']}"
            for e in entry['entries']
        ]


class PFSpellCardData(PFCardData):
    
    @property
    def header(self):
        return [
            "p2e_start_trait_section",
            *map("p2e_trait | common | {}".format, map(str.capitalize, self["traits"])),
            "p2e_start_trait_section",
            "ruler",
            *starmap("property | {} | {}".format, self.spell_properties)
        ]
    

    @property
    def spell_properties(self):
        raw = (
            ("Domain", " ".join(self.get("domains", [])) or None),
            ("Traditions", " ".join(self.get("traditions", [])) or None),
            ("Cast", self.spell_cast),
            ("Area", self.spell_area),
            ("Range", self.spell_range),
            ("Duration", self.spell_duration),
            ("Targets", self.get("targets")),
            ("Saving Throw", self.saving_throw),
        )

        return [(k, v) for k, v in raw if v is not None]
    
    @property
    def spell_cast(self):
        components = list(itertools.chain(*self["components"]))
        components += [] if "requirements" not in self else [self["requirements"]]
        return ", ".join(components)
    
    @property
    def spell_range(self):
        if "range" in self:
            return "{number} {unit}".format(**self["range"])
        
    @property
    def spell_area(self):
        if "area" in self:
            return self["area"].get("entry")
        
    @property
    def spell_duration(self):
        if "duration" not in self:
            return
        match self["duration"]:
            case {"unit": "special", "entry": duration}:
                return duration
            case duration:
                return "{number} {unit}".format(**duration)
    
    @property
    def saving_throw(self):
        if "savingThrow" not in self:
            return
        prefix = "basic " if self["savingThrow"].get("basic", False) else ""
        throws_format = "{}" if len(self["savingThrow"]["type"]) < 2 else "({})"

        return prefix + throws_format.format(", ".join(map(self.get_saving_throw, self["savingThrow"]["type"])))

    
    @staticmethod
    def get_saving_throw(short):
        match short:
            case "F":
                return "Fortitude"
            case "W":
                return "Will"
            case "R":
                return "Reflex"
            case _:
                raise ValueError(f"Unsupported Saving Throw Type: {short}")


    @property
    def heightened(self):
        match self.get("heighened"):
            case {"X": details}:
                return [
                    f"property | Heightened ({level}) | {' '.join(entries)}"
                    for level, entries in details.items()
                ]

            case {"plusX": details}:
                return [
                    f"property | Heightened (+{level}) | {' '.join(entries)}"
                    for level, entries in details.items()
                ]
        return []

    @property
    def footer(self):
        return [
            *map(self.scrub_refs, self.heightened)
        ]

    @property
    def body(self):
        return super().body + list(map(self.scrub_refs, self.footer))

def testing_func():
    import records
    import utils
    import json
    import formatting
    spells = ["Dragon Breath", "Aberrant Whispers", "Read Fate", "Power Word Blind", "Prismatic Spray", "Foresight"]
    pf2edata = records.PF2eToolsData(utils.get_env_variable("PATHFINDER_DATA_PATH"))
    spell_data = [
        PFSpellCardData(pf2edata.spells.query_record(name=spell, sources=["CRB"]))
        for spell in spells
    ]
    pairs = [
        pair
        for card_data in spell_data
        for pair in card_data.get_card_pairs(height=45, width=20)
    ]
    pages = formatting.CardPage.from_pairs(card_pairs=pairs, height=3, width=3)
    cards = [
        card
        for page in pages
        for card in formatting.CardPage.export(page)
    ]
    print(json.dumps(cards, indent=4))


if __name__ == "__main__":
    testing_func()