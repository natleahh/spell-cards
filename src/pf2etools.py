
from itertools import starmap
import itertools
import json
import logging 
from pathlib import Path
import re
from character import Build
from formatting import CardData, CardPage
from records import PF2eToolsData, TTRPGRecords
import utils

logger = logging.getLogger(__name__)

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


class Pathbuilder(Build):
	"""Pathbuild character build."""

	@classmethod
	def from_json_id(cls, id: int):
		"""Creates a pathbuilder buils from a JSON id."""
		headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0", "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
		return cls._from_url(
			url_format="https://pathbuilder2e.com/json.php?id={:06d}",
			format_params=(id,),
			headers=headers,
			data_path="$.build",
		)
	
		
	@classmethod
	def from_json(cls, json_data: str):
		"""Creates a pathbuilder buils from JSON string data."""
		return cls._from_json_data(
			json_data=json_data,
			data_path="$.build",
		)
	
	def meets_requirements(self, ttrpg_record: bool) -> bool:
		"""For provided Basic Action, bool for whether self meets the Actions proficieny requirements."""
		if (action_info := ttrpg_record.get("actionType")) is None:
			return False
		if not action_info["basic"]:
			return False
		
		skill_reqs = itertools.chain(
			itertools.product([level], skills)
			for level, skills in action_info.get("skill", {}).items()
		)
	
		for level, skill in skill_reqs:
			if utils.static.PROFICIENCY_LEVELS[level] <= self["proficiency"][skill]:
				return True
		
		return False
		

	@property
	def focus(self):
		""":list[str]: List of Focus spell names."""
		return [
			focus
			for attrfocus in self["focus"].values()
			for focus_details in attrfocus.values()
			for focus in itertools.chain(
				focus_details["focusCantrips"], 
				focus_details["focusSpells"]
			)
		]
	
	@property
	def feats(self):
		""":list[str]: List of Feat names."""
		return [feat_name for feat_name, *_ in self["feats"]]

	@property
	def spells(self):
		""":list[str]: List of Spell names."""
		return [
			spell
			for spell_caster in self.get("spellCasters", [])
			for spell_level in spell_caster["spells"]
			for spell in spell_level["list"]
		]
	
def get_spell_cards(
		json_path: Path | None, 
		json_id: int | None, 
		names: list[str] | None, 
		card_params: dict,
		page_layout: tuple[int, int], 
		card_layout: tuple[int, int]
	):
	"""Prints RPGCards to the command line.

	Args:
		json_path (Path | None): Path to a character JSON File.
		json_id (int | None): _Pathbuilder Character JSON ID.
		names (list[str] | None): _List of Spell Names.
		card_params (dict): Card Parameter Dictionary.
		page_layout (tuple[int, int]): Page layout dimentions.
		card_layout (tuple[int, int]): _Card Layout dimentions.
	"""

	## Extract Names
	data_source = PF2eToolsData(utils.get_env_variable("PATHFINDER_DATA_PATH"))
	records = TTRPGRecords.combine([data_source.spells, data_source.actions])
	if names:
		spell_names = names
	else:
		if json_id:
			build = Pathbuilder.from_json_id(json_id)
		elif json_path:
			build = Pathbuilder.from_json(json_path.read_text())
		else:
			raise ValueError("One of names, json_path or json_id must be provided.")
		spell_names = [*build.spells, *build.focus]
	

	## Query Data
	card_pairs = []
	c_h, c_w = card_layout
	for name in spell_names:
		try:
			spell = PFSpellCardData(records.query_record(name, ["PC1", "PC2"]))
		except (KeyError, IndexError):
			logger.warning(f"Unable to find TTRPG Record: {name} in PC1 or PC2.")
		card_pairs.extend(spell.get_card_pairs(height=c_h, width=c_w, **card_params))

	## Page formatting
	p_h, p_w = page_layout
	rpg_card_data = []
	for page in CardPage.from_pairs(card_pairs=card_pairs, height=p_h, width=p_w):
		rpg_card_data.extend(page.export())

	print(json.dumps(rpg_card_data, indent=4))
