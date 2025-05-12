""""""

from itertools import starmap
import itertools
import logging
from formatting import CardData
import utils
from utils import static

logger = logging.getLogger(__name__)

class Card(CardData):
	"""Class to handle conversion between DnD5e TTRPG Records and cards."""
	

	@property
	def body(self):
		""":list[str]: Text body."""
		return super().body + list(map(self.scrub_refs, self.footer))
	


class SpellCard(Card):
	"""Class to handle conversion between DnD5e Spell TTRPG Records and cards."""

	@property
	def tags(self):
		raw = [
	  		*super().tags,
			"spell",
			self.get("spell_source"),
			self.school,
			self.level,
		]
		return [tag for tag in raw if tag is not None]

	@property
	def icon(self):
		""":str: Space separated list of icon names."""
		return f"white-book-{self['level']}"
		
	@property
	def header(self):
		""":list[str]: header text."""
		return [
			f"subtitle | {self.level.capitalize()} {self.school.capitalize()}",
			*starmap("property | {} | {}".format, self.spell_properties),
			"rule"
		]
  
	@property
	def level(self):
		""":str: Spell level as wordsd."""
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

	@property
	def school(self):
		""":str: Spell school name."""
		try:
			return static.SCHOOL_MAPPING[self["school"]]
		except KeyError:
			raise KeyError(f"Abbreviated school {self['school']} in spell {self['name']} doesn't have mapped name.")
 	

	@property
	def spell_properties(self):
		""":list[tuple[str, str]]: Spell properties."""
		raw = (
			("Casting Time", self.casting_time),
			("Range", self.range),
			("Components", self.components),
			("Duration", self.duration)
		)

		return [(k, v) for k, v in raw if v is not None]
 
	@property
	def casting_time(self):
		""":str: Spell casting time."""
		return ", ".join(
			"{number} {unit}".format(**each)
			for each in self["time"]
		) or None
		
	@property
	def range(self):
		""":str: Spell range name."""
		match self["range"]:
			case None:
				return None
			case {"type": "special", **__}:
				return "special"
			case {"type": shape, "distance": details}:
				shape = "from a point" if shape == "point" else shape
				match details:
					case {"type": "touch"}:
						return "touch"
					case {"type": type, "amount": amount}:
						return f"{amount} {type} {shape}"
			case _:
				raise ValueError(f"Unsupported range type: {self['range']['type']} for spell {self['name']}")
			
	@property
	def components(self):
		""":str: List of Spell components."""
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

	@property
	def duration(self):
		""":str: Spell duration."""
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
	

	@property
	def heightened(self):
		""":listr[str]: Heightened text lines.."""
		hightened_entries = list(map(self.handle_entry, self.get("entriesHigherLevel", [])))
		return list(itertools.chain.from_iterable(hightened_entries))


	@property
	def footer(self):
		""":list[str]: Text footer."""
		return [
			*map(self.scrub_refs, self.heightened)
		]

class MagicItemCard(Card):
    
    
	
	@property
	def tags(self):
		return super().tags + ["magic_item"]

	@property
	def footer(self):
		if (max_charges := self.get("charges")) is None:
			return []
		elif max_charges <= 20:
			charges_row = f"boxes | {max_charges} | 1.5"
		else:
			charges_row = "description | Current Charges: |"
		return ["rule", charges_row]
	
	@property
	def header(self):
		traits =  [
			f"subtitle | {self.subtitle}",
			"rule"
		]
		if not self.properties:
			return traits
		for property_name, value in self.properties:
			traits.append(f"property | {property_name} | {value}")
		return [*traits, "rule"]

	@property
	def attunement(self):
		match self.get("reqAttune"):
			case True:
				return "requires attunement"
			case False | None:
				return None
			case _:
				return f"requires attunement {self['reqAttune']}"
	
	@property
	def subtitle(self):
		requirement = f"({self.attunement})" if self.attunement else ""
		base_time = self.get("baseItem", "wonderous item")
		return f"{base_time.title()} {requirement.title()}"

 
	@property
	def properties(self):
		property_names = ["rarity", "tier", "charges"]
		return [
			(name.capitalize(), self[name])
			for name in property_names
			if self.get(name)
		]