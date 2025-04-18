
from collections import UserDict
import json

from jsonpath_ng.ext import parse
import requests



class BaseBuild(UserDict):
    """Class for ingesting JSON character data."""

    @classmethod
    def _from_url(cls, url_format: str, format_params: tuple, headers: dict = None,  data_path: str = "$"):
        """Pulls character data from URL and JSON Path."""
        url = url_format.format(*format_params)
        with requests.get(url, headers=headers) as response:
            response.raise_for_status()
            return cls._from_json_data(json_data=response.text, data_path=data_path)
        

    
    @classmethod
    def _from_json_data(cls, json_data: str, data_path: str = "$"):
        """Pulls character data from JSON data and JSON path."""
        build_data, *_ = parse(data_path).find(json.loads(json_data))
        return cls(build_data.value)



