
from itertools import starmap
import itertools
import re
from formatting import CardData


class PFCardData(CardData):
	"""Class to handle conversion between PF2e TTRPG Records and cards."""


	@classmethod
	def handle_entry(cls, entry: str | dict) -> list[str]:
		"""Converts TTRPG entry to RPGCard compatible line.

		Args:
			entry (list | dict): TTRPG entry

		Raises:
			ValueError: If unsupported entry type is supplied.
		"""
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
		"""Converts camelcase strings to scpace separated words."""
		return '_'.join(
			re.sub('([A-Z][a-z]+)', r' \1',
			re.sub('([A-Z]+)', r' \1',
			string.replace('-', ' '))).split()).lower()
	
	@staticmethod
	def get_sub_paragraph_details(entry, keys):
		"""Returns a paragraph for subparagraph."""
		return " ".join(
			f"<b>{PFCardData.camel_to_words(key)}:</b> {entry[key]}"
			for key  in keys
		)
	
	@classmethod
	def to_affiction(cls, entry):
		"""Converts an affiliction entry to a text line."""
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
		"""Converts an ability entry to an text line."""
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
		"""Converts an upcast entry to a text line."""
		return [
			f"property | {e['range']} | {e['entry']}"
			for e in entry['entries']
		]


class PFSpellCardData(PFCardData):
	"""Class to handle conversion between PF2e Spell TTRPG Records and cards."""


	@property
	def icon(self):
		""":str: Space separated list of icon names."""
		match self["cast"]:
			case {"unit": "action", "number": n}:
				match n:
					case 0:
						icons = ["p2e-free-action"]
					case 1: 
						icons = [f"p2e-1-action"]
					case n:
						icons = [f"p2e-{n}-actions"]
			case {"unit": "reaction", **__}:
				icons = ["p2e-reaction"]
			case _:
				icons = []
		return " ".join([f"white-book-{self['level']}", *icons])
		
	
	@property
	def header(self):
		""":list[str]: header text."""
		return [
			"p2e_start_trait_section",
			*map("p2e_trait | common | {}".format, map(str.capitalize, self["traits"])),
			"p2e_end_trait_section",
			"p2e_ruler",
			*starmap("property | {} | {}".format, self.spell_properties),
			"p2e_ruler",
		]
	

	@property
	def spell_properties(self):
		""":list[tuple[str, str]]: Spell properties."""
		raw = (
			("Level", self["level"]),
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
	def spell_cast_time(self):
		""":str: Casting Time."""
		return "{number} {unit}".format(**self["cast"])

	
	@property
	def spell_cast(self):
		""":str: Casting Requirements."""
		components = list(itertools.chain(*self.get("components", [])))
		components += [] if "requirements" not in self else [self["requirements"]]
		return f"{self.spell_cast_time}  {', '.join(components)}"
	
	@property
	def spell_range(self):
		""":str: Spell range:"""
		if "range" in self:
			return "{number} {unit}".format(**self["range"])
		
	@property
	def spell_area(self):
		""":str: Spell area."""
		if "area" in self:
			return self["area"].get("entry")
		
	@property
	def spell_duration(self):
		""":str: Spell duration."""
		if "duration" not in self:
			return
		match self["duration"]:
			case {"unit": "special", "entry": duration}:
				return duration
			case duration:
				return "{number} {unit}".format(**duration)
	
	@property
	def saving_throw(self):
		""":str: Spell saving throw."""
		if "savingThrow" not in self:
			return
		prefix = "basic " if self["savingThrow"].get("basic", False) else ""
		throws_format = "{}" if len(self["savingThrow"]["type"]) < 2 else "({})"

		return prefix + throws_format.format(", ".join(map(self.get_saving_throw, self["savingThrow"]["type"])))

	
	@staticmethod
	def get_saving_throw(short):
		"""Returns long saving throw name to long."""
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
		""":listr[str]: Heightened text lines.."""
		match self.get("heightened"):
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
		""":list[str]: Text footer."""
		return [
			*map(self.scrub_refs, self.heightened)
		]

	@property
	def body(self):
		""":list[str]: Text body."""
		return super().body + list(map(self.scrub_refs, self.footer))

