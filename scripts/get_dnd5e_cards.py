
import argparse
import json
from pathlib import Path
import sys
from typing import Optional

from titlecase import titlecase

from spellcard_dataclasses import custom, dndbeyond


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
        type=lambda s: titlecase(s.replace("_", " ")),
        nargs="+"
    )
    
    parser.add_argument(
        "--outpath", "-o",
        type=str,
    )
    return parser.parse_args(argv)

def main(argv: Optional[list[str]] = None):
    args = parse_cli_args(argv)
    if args.spell_names:
        spells = custom.Dnd5eSpells.from_spell_names(args.spell_names)
    else:
        if args.character_json_id:
            build = dndbeyond.Build.from_json_id(args.character_json_id)
        elif args.character_json_path:
            build = dndbeyond.Build.from_json_data(args.character_json_path.read_text())
        spells = custom.Dnd5eSpells.from_dndbeyond_build(build)
        

    cards = spells.get_all_cards()

    with (open(args.outpath, "w") if args.outpath is not None else sys.stdout) as output:
        json.dump(cards, output, indent=4)
            

if __name__ == "__main__":
    main()