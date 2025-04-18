""""""

import itertools
import logging
from character import BaseBuild
import utils


logger = logging.getLogger(__name__)

class Pathbuilder(BaseBuild):
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
	
