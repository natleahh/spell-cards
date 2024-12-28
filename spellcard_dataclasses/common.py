import json
from typing import TypedDict

import requests


class StructCommon(dict):
    STRUCTURE: type[TypedDict] = TypedDict
        
    @classmethod
    def from_raw_dict(cls, raw_dict):
        return cls(cls.STRUCTURE(raw_dict))
    
class CommonBuild(StructCommon):
    
    @classmethod
    def _from_json_data(cls, json_data: str, data_key: str):
        return cls.from_raw_dict(json.loads(json_data)[data_key])
    
    @classmethod
    def _from_url(cls, data_key: str, url_format: str, format_params: tuple, headers: dict = None,):
        url = url_format.format(*format_params)
        with requests.get(url, headers=headers) as response:
            response.raise_for_status()
            return cls._from_json_data(json_data=response.text, data_key=data_key)
    
    