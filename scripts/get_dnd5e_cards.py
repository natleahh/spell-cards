
import argparse
from itertools import chain
import json
from pathlib import Path
import sys
from typing import Optional
from spellcard_dataclasses import card, dnd5etools, dndbeyond
import utils


def parse_cli_args(argv: Optional[list[str]]):
    parser = argparse.ArgumentParser()

    data_input = parser.add_mutually_exclusive_group(required=True)

    data_input.add_argument(
        "--character_json_id",
        type=int
    )

    data_input.add_argument(
        "--character_json_path",
        type=Path,
    )
    data_input.add_argument(
        "--spell_names",
        type=lambda s: utils.custom_titlecase(s.replace("_", " ")),
        nargs="+"
    )
    data_input.add_argument(
        "--statblock_data_path",
        type=Path,
    )
    
    parser.add_argument(
        "--color",
        type=str,
    )
    
    parser.add_argument(
        "--page_layout",
        type=lambda s: tuple(",".split(s)),
        default=(3, 3)
    )
    
    parser.add_argument(
        "--outpath", "-o",
        type=str,
    )
    return parser.parse_args(argv)

def main(argv: Optional[list[str]] = None):
    args = parse_cli_args(argv)
    if args.spell_names:
        spells = card.Dnd5eSpells.from_spell_names(args.spell_names)
    elif args.statblock_data_path:
        statblocks = dnd5etools.Monster.from_source_data(args.statblock_data_path.read_text())
        spell_names = chain.from_iterable(map(dnd5etools.Monster.get_spell_names, statblocks))
        spells = card.Dnd5eSpells.from_spell_names(spell_names=spell_names)
    else:
        if args.character_json_id:
            build = dndbeyond.Build.from_json_id(args.character_json_id)
        elif args.character_json_path:
            build = dndbeyond.Build.from_json_data(args.character_json_path.read_text())
        spells = card.Dnd5eSpells.from_dndbeyond_build(build)
    
        
    spells.set_color(args.color)
    spells.set_page_layout(args.page_layout)
    cards = spells.get_all_cards()

    with (open(args.outpath, "w") if args.outpath is not None else sys.stdout) as output:
        json.dump(cards, output, indent=4)
            

if __name__ == "__main__":
    main()