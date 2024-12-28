
import argparse
import json
from pathlib import Path
import sys
from typing import Optional

from spellcard_dataclasses.custom import PathFinderActions
from spellcard_structs.pathbuilder import Build


def parse_cli_args(argv: Optional[list[str]]):
    parser = argparse.ArgumentParser()

    data_input = parser.add_mutually_exclusive_group(required=True)

    data_input.add_argument(
        "--json_id",
        type=int
    )

    data_input.add_argument(
        "--json_path",
        type=Path,
    )
    
    parser.add_argument(
        "--outpath", "-o",
        type=str,
    )
    return parser.parse_args(argv)

def main(argv: Optional[list[str]] = None):
    args = parse_cli_args(argv)
    if args.json_id:
        build = Build.from_json_id(args.json_id)
    else:
        build = Build.from_json(args.json_path.read_text())

    character = PathFinderActions.from_pathbuilder_build(build)
    cards = character.get_all_cards()

    with (open(args.outpath, "w") if args.outpath is not None else sys.stdout) as output:
        json.dump(cards, output, indent=4)
            

if __name__ == "__main__":
    main()