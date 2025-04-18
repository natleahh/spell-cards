from collections import UserDict
from copy import deepcopy
import itertools
import json
import re


class CardData(UserDict):
	"""Class to handle conversion between TTRPG Records and cards."""

	@staticmethod
	def scrub_refs(text: str):
		"""Removes references from text."""
		return re.sub(r"\{@\w+ ([^}]+)\}", r"\1", text)		

	@property
	def body(self):
		""":str: Body text."""
		raw = [*itertools.chain(*map(self.handle_entry, self["entries"]))]
		return list(map(self.scrub_refs, raw))


	@property
	def header(self):
		""":str: header text."""
		raise NotImplementedError(f"No property method implemented for {type(self).__name__}. Please implement one.")

	@property
	def name(self):
		""":str: Card data name."""
		return self["name"]

	@property
	def icon(self):
		""":str | None: Card Icon."""
		return None
	
	@property
	def card_params(self):
		""":dict: Default card parameters."""
		return {"count": 1, "icon": self.icon}



	@classmethod
	def handle_entry(cls, entry: list | dict):
		"""
		Converts TTRPG entry to RPGCard compatible line.

		Args:
			entry (list | dict): TTRPG entry

		Raises:
			ValueError: If unsupported entry type is supplied.
		"""
		if isinstance(entry, str):
			return[ f"text | {entry}"]
		match entry["type"]:
			case "list":
				title, *bullets = entry["items"]
				return [
					f"text | {title}",
					*map("bullet | {}".format, bullets)
				]
			case "entries":
				return [
					f"text | <b>{entry['name']}</b>",
					*map(cls.handle_entry, entry["entries"])
				]
			case "table":
				return ["text | <b> See source table </b> | "]
			case "inset" | "quote":
				return []
			case _:
				cls._raise_entry(entry)

	@classmethod
	def get_block_height(cls, line: str, width: int):
		"""Returns the approximate height of a line if confirming to the provided width.

		Args:
			line (str): Text line.
			width (int): Card width in approximate characters.

		Raises:
			ValueError: If line is an unexpected format.
		"""
		tabbed_padding = 0
		end_padding = 0
		line_length = 0
		match line.split(" | "):
			case ["rule" | "ruler" | "p2e_ruler"]:
				return 1.0
			case ["property", property_name, text_body]:
				content = f"{property_name} {text_body}"
				tabbed_padding = 2
			case ["text", content]:
				end_padding = 1
			case ["bullet", content]:
				line_length = 4
				tabbed_padding = 4
			case ["boxes", number, size]:
				return ((int(number) * float(size))  // 15) + 1
			case ["p2e_start_trait_section"] | ["p2e_trait", _, _]:
				return 0
			case ["p2e_end_trait_section"]:
				return 2
			case ["p2e_activity", _, _, content]:
				tabbed_padding = 2
			case [_, _]:
				pass
			case unhandled:
				raise ValueError(f"Unhandled entry type case:\n{unhandled}")
		size = 0
		for word in content.split(" "):
			word_length = len(word) + 1
			if line_length + word_length > width:
				size += 1
				line_length = tabbed_padding
			line_length += word_length
		return size + end_padding + (line_length / width)

	
	def split_body(self, height: int, width: int):
		"""Splits body into units to provided card dimentions.

		Args:
			height (int): Card height in approximate lines.
			width (int): Card width in approximate characters.
		"""
		header_size = sum(self.get_block_height(line, width=width) for line in self.header)
		line_count = header_size
		content = deepcopy(self.body)
		sublists = [[]]
		while content:
			line = content.pop(0)
			block_size = self.get_block_height(line=line, width=width)
			if block_size + line_count > height:
				*head, text = line.split(" | ")
				line_overspill = height - (block_size + line_count)
				char_overspill = int(line_overspill * width) - len("(cont.)")
				try:
					while line[char_overspill] != " ":
						char_overspill -= 1
				except IndexError:
					char_overspill = 0
				front, back = text[:char_overspill], text[char_overspill:]
				if front:
					sublists[-1].append(f"{' | '.join([*head, front])} (cont.)")
				line_count = header_size
				if back:
					content.insert(0, f"{' | '.join([*head, '(cont.) ' + back])}")
				sublists.append([])
			else:
				sublists[-1].append(line)
				line_count += int(block_size)
		return [*filter(bool, sublists)]

	def get_card_pairs(self, height: int, width: int, **card_params):
		"""Produces front and back card pairs.

		Args:
			height (int): Card height in approximate lines.
			width (int): Card width in approximate characters.
			**card_params (dict): Parameters to be applied to card.

		"""
		# card data
		card_data = [
			[*self.header, *split_body]
			for split_body in self.split_body(height, width)
		]
		
		# card pairs
		card_data_pairs = [*itertools.zip_longest(card_data[::2], card_data[1::2], fillvalue=[])]

		n = len(card_data_pairs)
		card_index = (
    		[*itertools.starmap(" {}/{}".format, itertools.product(range(1, n + 1), [n]))]
			if n > 1 else [""]
		)

		default_params = self.card_params | card_params

		return [
			tuple(
				{"title": self.name + card_index[i], "contents": content} | default_params if content else  default_params
				for content in card_pair
			)
			for i, card_pair in enumerate(card_data_pairs)
		]
	
	@staticmethod
	def _raise_entry(entry: dict):
		"""Raises an Value error for a unssuprted entry type."""
		raise ValueError(f"Entry type: {entry['type']} is not supported.\n{json.dumps(entry, indent=4)}")

class CardPage(tuple[tuple[dict, ...], ...]):
	"""Class for formatting, controlling and outputting pages of cards."""

	@classmethod
	def from_pairs(cls, card_pairs: list[tuple[dict, dict]], height: int, width: int):
		"""Intilises formatted pages from a list of card pairs, and provided page dimentions.

		Args:
			card_pairs (list[tuple[dict, dict]]): List of paired cards fronts and backs.
			height (int): Page height in cards.
			width (int): Page width in cards.
		"""
		page_max = height * width

		pages = []

		for batch in itertools.batched(card_pairs, n=page_max):
			listed = zip(*batch)
			front_page, back_page = map(lambda xs: xs + ({},) * (page_max - len(xs)), listed)
			front = cls(cls.to_matrix(*front_page, height=height, width=width))
			back = cls(cls.flip_h(cls.to_matrix(*back_page, height=height, width=width)))
			pages.extend([front, back])
		
		return pages
	
	@staticmethod
	def to_matrix(*cards, height, width):
		"""Returns a height by width matrixs of cards."""
		return tuple(
			tuple(*itertools.batched(row, n=width))
			for row in itertools.batched(cards, n=height)
		)	
    
	@staticmethod
	def flip_h(page: tuple[tuple[dict, ...], ...]):
		"""Horizontally flips provided page."""
		return tuple(row[::-1] for row in page)
	
	 
	def export(self):
		"""Returns RPGCard compatible json list of formatted pages."""
		return [*itertools.chain.from_iterable(self)]
    
