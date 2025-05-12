""""""

from functools import cached_property
import itertools
import logging
from character import BaseBuild


logger = logging.getLogger(__name__)

class DnDBeyond(BaseBuild):
	"""Pathbuild character build."""

	@classmethod
	def from_json_id(cls, id: int):
		"""Creates a pathbuilder buils from a JSON id."""
		return cls._from_url(
			url_format="https://character-service.dndbeyond.com/character/v5/character/{:08d}",
			format_params=(id,),
			data_path="$.data",
		)
	
		
	@classmethod
	def from_json(cls, json_data: str):
		"""Creates a pathbuilder buils from JSON string data."""
		return cls._from_json_data(
			json_data=json_data,
			data_path="$.data",
		)

	@property
	def spell_data(self):
		""":list[dict]: List of DnDBeyond Spell entities."""
		return list(itertools.chain(
			itertools.chain.from_iterable(classSpell.get("spells") for classSpell in self["classSpells"]),
			*filter(bool, self["spells"].values())
		))
  

	@staticmethod
	def get_id_name(item: dict):
		"""Returns a tuple of entity ID and name."""
		return item["definition"]["id"], item["definition"]["name"]

	@cached_property
	def source_map(self):
		""":dict[int, str]: Mapping of IDs and Names for DnDEntity sources."""
		sources = []

		# class features
		for char_class in self["classes"]:
			sources.extend(map(self.get_id_name, char_class["classFeatures"]))

		# spells from magic items
		sources.extend(map(self.get_id_name, self["inventory"]))

		return dict(sources)

	@property
	def spells_with_sources(self):
		""":list[tuple[str, str]]: List of spells and spell sources."""
		return [
			(spell["definition"]["name"], self.source_map.get(spell.get("componentId")))
			for spell in self.spell_data
		]

	@property
	def magic_items(self):
		""":list[str]: List of magic items."""
		return [
			item["definition"]["name"]
			for item in self["inventory"]
			if item["definition"].get("magic", False)
		]
