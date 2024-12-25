
from functools import cache
import json
from typing import TypedDict

import requests

import utils.static as static


class Feat(list[str]):
    
    @property
    def name(self):
        return self[0]

class Build(TypedDict):
    level: int
    feats: list[Feat]
    specials: list[str]
    proficiencies: dict[str, int]
    
    @staticmethod
    def from_json_id(id: int):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0", "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        with requests.get(f"https://pathbuilder2e.com/json.php?id={id:06d}", headers=headers) as response:
            response.raise_for_status()
            return Build.from_json(response.text)
    
    @staticmethod
    def from_json(json_data: str):
        build_data = json.loads(json_data)["build"]
        return Build(
            level=build_data["level"],
            feats=list(map(Feat, build_data["feats"])),
            specials=build_data["specials"],
            proficiencies=build_data["proficiencies"]
        )
    
    def get_all_feat_names(self):
        return [
            *[feat.name for feat in self["feats"]],
            *self["specials"]
        ]
    
    def get_proficiency_map(self):
        return {
            name: static.BASE_PROFICIENCY_MAP[value - self["level"]]
            for name, value 
            in self["proficiency"].items()
        }