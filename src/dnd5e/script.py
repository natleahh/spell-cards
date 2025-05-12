""""""

import itertools
import json
import logging
from pathlib import Path


from dnd5e.card import MagicItemCard
from formatting import CardPage
from dnd5e import SpellCard, DnDBeyond
from records import Dnd5eToolsData, TTRPGRecords
import utils

logger = logging.getLogger(__name__)

def get_spell_cards(
		json_path: Path | None = None, 
		json_id: int | None = None, 
		names: list[str] | None = None, 
		card_params: dict = None,
		page_layout: tuple[int, int] = None, 
		card_layout: tuple[int, int] = None,
	):
	"""Prints RPGCards to the command line.

	Args:
		json_path (Path | None): Path to a character JSON File.
		json_id (int | None): DnDBeyond Character JSON ID.
		names (list[str] | None): _List of Spell Names.
		card_params (dict): Card Parameter Dictionary.
		page_layout (tuple[int, int]): Page layout dimentions.
		card_layout (tuple[int, int]): _Card Layout dimentions.
	"""

	## Extract Names
	data_source = Dnd5eToolsData(utils.get_env_variable("DND_DATA_PATH"))
	records = data_source.spells
	if names:
		spell_and_source = list(itertools.product(names, [None]))
	else:
		if json_id:
			build = DnDBeyond.from_json_id(json_id)
		elif json_path:
			build = DnDBeyond.from_json(json_path.read_text())
		else:
			raise ValueError("One of names, json_path or json_id must be provided.")
		spell_and_source = build.spells_with_sources
	

	## Query Data
	card_pairs = []
	c_h, c_w = card_layout
	for name, source in spell_and_source:
		try:
			record = records.query_record(name)
			if source is not None:
				record["name"] += f" ({source})"
				records["spell_source"] = source
			spell = SpellCard(record)
		except (KeyError, IndexError):
			logger.warning(f"Unable to find TTRPG Record: {name} in PC1 or PC2.")
		card_pairs.extend(spell.get_card_pairs(height=c_h, width=c_w, **card_params))

	## Page formatting
	p_h, p_w = page_layout
	rpg_card_data = []
	for page in CardPage.from_pairs(card_pairs=card_pairs, height=p_h, width=p_w):
		rpg_card_data.extend(page.export())

	print(json.dumps(rpg_card_data, indent=4))


def get_magic_item_cards(
		json_path: Path | None = None, 
		json_id: int | None = None, 
		names: list[str] | None = None, 
		card_params: dict = None,
		page_layout: tuple[int, int] = None, 
		card_layout: tuple[int, int] = None,
	):
	"""Prints RPGCards to the command line.

	Args:
		json_path (Path | None): Path to a character JSON File.
		json_id (int | None): DnDBeyond Character JSON ID.
		names (list[str] | None): _List of Spell Names.
		card_params (dict): Card Parameter Dictionary.
		page_layout (tuple[int, int]): Page layout dimentions.
		card_layout (tuple[int, int]): _Card Layout dimentions.
	"""

	## Extract Names
	data_source = Dnd5eToolsData(utils.get_env_variable("DND_DATA_PATH"))
	records = TTRPGRecords.combine([data_source.items, data_source.homebrew_items])
	if names:
		item_names = names
	else:
		if json_id:
			build = DnDBeyond.from_json_id(json_id)
		elif json_path:
			build = DnDBeyond.from_json(json_path.read_text())
		else:
			raise ValueError("One of names, json_path or json_id must be provided.")
		item_names = build.magic_items
	
	## Query Data
	card_pairs = []
	c_h, c_w = card_layout
	for name in item_names:
		try:
			spell = MagicItemCard(records.query_record(name))
		except (KeyError, IndexError):
			logger.warning(f"Unable to find TTRPG Record: {name} in Dnd Sources or Homebrew.")
		card_pairs.extend(spell.get_card_pairs(height=c_h, width=c_w, **card_params))

	## Page formatting
	p_h, p_w = page_layout
	rpg_card_data = []
	for page in CardPage.from_pairs(card_pairs=card_pairs, height=p_h, width=p_w):
		rpg_card_data.extend(page.export())

	print(json.dumps(rpg_card_data, indent=4))
 