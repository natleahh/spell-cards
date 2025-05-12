"""Module for manage package command line interface."""
import argparse
from pathlib import Path
from typing import Callable

from dnd5e import (
    get_spell_cards as dnd_spell,
    get_magic_item_cards as dnd_magic
)
from pathfinder2e import (
    get_spell_cards as pf2e_spell, 
    get_full_character_cards as pf2e_full
)


class TTRPGParentParser(argparse.ArgumentParser):
    """Argument Parser for TTRPG Cards."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.subparers = self.add_subparsers(title="subcommands")
        self.data_input = self.add_mutually_exclusive_group()

        self.data_input.add_argument(
            "--json_path", 
            type=Path,
            help="Path to a JSON Build."
        )
        self.data_input.add_argument(
            "--json_id",
            type=int,
            help="ID for JSON data in TTRPG Service."
        )

        self.add_argument(
            "--card_params",
            action=CardParamAction,
            nargs="*",
            help="Comma separated List of card parameters. Formatted `key1=val1 key2=val2`.",
            default={},
        )

        self.add_argument(
            "--card_layout",
            action=HWAction,
            help="Layout each hard in characters. Formatted as `H,W`. 45,20 by default.",
            default=(20, 40),
        )

        self.add_argument(
            "--page_layout",
            action=HWAction,
            help="Layout of card arragement for resultant page in cards. Formatted as `H,W`. 3,3 by default.",
            default=(3, 3),
        )


    def get_subparser(self, name: str, func: Callable, description: None | str = None):
        subparser = self.subparers.add_parser(name, description=description)
        subparser.data_input = self.data_input
        subparser.set_defaults(func=func)
        return subparser

def add_names_arg(parser: argparse.ArgumentParser):
        parser.data_input.add_argument(
            "--names",
            metavar="NAME",
            type=str,
            nargs="+",
            help="List of Space Separated TTRPG Record Names."
        )
        return parser

class CardParamAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string = None):
        params = dict(param.split("=") for param in values)
        setattr(namespace, self.dest, params)

class HWAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string = None):
        setattr(namespace, self.dest, tuple(map(int, values.split(","))))

def main(argv: None | list[str] = None):
    """Main Entrypoint to rpg-cards package."""
    
    parent_parser = TTRPGParentParser(
        prog="rpg_cards",
        description="A command line tool for generating https://rpg-cards.vercel.app/ compatible JSON data."
    )

    pf2espell_subparser = parent_parser.get_subparser(
        name="pf2espells",
        description="Creates Pathfinder 2e Spell cards from provided params.",
        func=pf2e_spell
    )
    add_names_arg(parser=pf2espell_subparser)

    parent_parser.get_subparser(
        name="pf2efullcharacter",
        description="Create Pathfinder 2e Spells, Feats and Basic Actions from provided params.",
        func=pf2e_full
    )

    parent_parser.get_subparser(
        name="dnd5espells",
        description="Creates DnD 5th Edition (2014) Spell cards from provided params.",
        func=dnd_spell
    )
    
    parent_parser.get_subparser(
        name="dnd5eitems",
        description="Creates DnD 5th Edition (2014) & Homebrew Magic Items cards from provided params.",
        func=dnd_magic
    )


    
    
    args = parent_parser.parse_args(argv)
    kwargs = dict(kw for kw in args._get_kwargs() if kw[0] not in ["func"])
    args.func(**kwargs)
