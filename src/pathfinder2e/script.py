""""""

import itertools
import json
import logging
from pathlib import Path


from formatting import CardPage
from pathfinder2e import BasicActionCard, FeatCard, SpellCard, Pathbuilder
from records import PF2eToolsData, TTRPGRecords
import utils

logger = logging.getLogger(__name__)

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
			spell = SpellCard(records.query_record(name, ["PC1", "PC2"]))
		except (KeyError, IndexError):
			logger.warning(f"Unable to find TTRPG Record: {name} in PC1 or PC2.")
		card_pairs.extend(spell.get_card_pairs(height=c_h, width=c_w, **card_params))

	## Page formatting
	p_h, p_w = page_layout
	rpg_card_data = []
	for page in CardPage.from_pairs(card_pairs=card_pairs, height=p_h, width=p_w):
		rpg_card_data.extend(page.export())

	print(json.dumps(rpg_card_data, indent=4))


def get_full_character_cards(
		json_path: Path | None, 
		json_id: int | None, 
		card_params: dict,
		page_layout: tuple[int, int], 
		card_layout: tuple[int, int],
		**_
	):
	"""Prints RPGCards to the command line.

	Args:
		json_path (Path | None): Path to a character JSON File.
		json_id (int | None): _Pathbuilder Character JSON ID.
		card_params (dict): Card Parameter Dictionary.
		page_layout (tuple[int, int]): Page layout dimentions.
		card_layout (tuple[int, int]): _Card Layout dimentions.
	"""

	## Extract Names
	data_source = PF2eToolsData(utils.get_env_variable("PATHFINDER_DATA_PATH"))
	records = TTRPGRecords.combine([data_source.spells, data_source.actions, data_source.feats])
	if json_id:
		build = Pathbuilder.from_json_id(json_id)
	elif json_path:
		build = Pathbuilder.from_json(json_path.read_text())
	else:
		raise ValueError("One of json_path or json_id must be provided.")
	
	cards = []

	## Filter Basic Actions Index
	basic_actions = [
		BasicActionCard(action_data.dropna().to_dict())
		for source in ["PC1", "PC2"]
		for _, action_data in data_source.actions.loc[(slice(None), source), :].reset_index().iterrows()
		if build.meets_requirements(action_data.dropna().to_dict())
	]
	cards.extend(basic_actions)

	## Filter Feats
	for name in build.feats:
		try:
			feat_data = records.query_record(name, ["PC1", "PC2"])
			cards.append(FeatCard(feat_data))
		except (KeyError, IndexError):
			logger.warning(f"Unable to find TTRPG Record: {name} in PC1 or PC2.")
			continue

	## Query Spells
	for name in [*build.spells, *build.focus]:
		try:
			spell_data = records.query_record(name, ["PC1", "PC2"])
			cards.append(SpellCard(spell_data))
		except (KeyError, IndexError):
			logger.warning(f"Unable to find TTRPG Record: {name} in PC1 or PC2.")
			continue


	## Query Data
	c_h, c_w = card_layout
	card_pairs = itertools.chain.from_iterable(
		card.get_card_pairs(height=c_h, width=c_w, **card_params)
		for card in cards
	)

	## Page formatting
	p_h, p_w = page_layout
	rpg_card_data = []
	for page in CardPage.from_pairs(card_pairs=card_pairs, height=p_h, width=p_w):
		rpg_card_data.extend(page.export())

	print(json.dumps(rpg_card_data, indent=4))
