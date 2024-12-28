import json

import requests
from spellcard_dataclasses import common
from spellcard_structs import pathbuilder
from utils import sources

class Feat(pathbuilder.Feat):
	
	@property
	def name(self):
		return self[0]

class Build(common.CommonBuild):
    
    STRUCTURE = pathbuilder.Build
	
    @classmethod
    def from_json_id(cls, id: int):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0", "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        return cls._from_url(
            "build",
            "https://pathbuilder2e.com/json.php?id={:06d}",
            (id,),
            headers=headers,
        )
    
    @classmethod
    def from_json(cls, json_data: str):
        return cls._from_json_data(
            json_data,
            "build",
        )
    
    def get_all_feat_names(self):
        return [
            *[feat[0] for feat in self["feats"]],
            *self["specials"]
        ]
    
    def get_proficiency_map(self):
        return {
            name: sources.PROFICIENCY_BY_BONUS[value]
            for name, value 
            in self["proficiencies"].items()
        }