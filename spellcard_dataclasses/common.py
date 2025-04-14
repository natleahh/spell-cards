import json
import logging
import re
from typing import Self, TypedDict, Optional

import pandas as pd
import requests


class StructCommon(dict):
    STRUCTURE: type[TypedDict]
        
    @classmethod
    def from_raw_dict(cls, raw_dict):
        return cls(cls.STRUCTURE(raw_dict))

POSESSIVE_FILTER = re.compile("\w+'s ")

class LegacySupport:

    LEGACY_CHANGES = [
        (r"(.*)Tripkee(.*)", "\g<1>Grippli\g<2>"),
        (r"Stunning Blows", "Stunning Fist"),
        (r"(Hideous Laughter)", "Tasha's \g<1>"),
        (r"Arcane Hand", "Bigby's Hand"),
        (r"Telepathic Bond", "Rary's Telepathic Bond")
]
    
    @classmethod
    def legacy_compatbility(cls, name):
        for pattern, sub in cls.LEGACY_CHANGES:
            if re.match(pattern, name) is None:
                continue
            return re.sub(pattern, sub, name)
        return name

    
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
    
    
class DBItemCommon(StructCommon, LegacySupport):
    SOURCES: list
    DATA: pd.DataFrame
    
    @classmethod
    def all_from_build(cls, build: CommonBuild) -> list[str]:
        raise NotImplementedError()
            
    @classmethod
    def from_name(cls, name: str, source: Optional[str] = None): # type: ignore
        name = cls.legacy_compatbility(name)
        try: 
            query = cls.DATA.loc[name]
        except KeyError:
            name_index = cls.DATA.index.get_level_values("name")
            selector = name_index.map(str.lower) == name.lower()
            if not selector.any():
                logging.error(f"No record called {name} in database.")
                return
            query = cls.DATA[selector]
        except KeyError:
            logging.error(f"No record called {name} in database.")
            return
        if query.index.size > 1:
            try:
                query = query.loc[source].head(1)
            except:
                query = query.sort_values(
                    by="source",
                    key=lambda col: col.map(lambda v: 255 if v not in cls.SOURCES else cls.SOURCES.index(v))
                ).head(1)
                source = query.index.to_list()[0][0]
        raw_dict = query.replace(float("nan"), None).squeeze().to_dict()
        return cls.from_raw_dict(raw_dict={"name": name, "source": raw_dict.get("source") or source, **raw_dict})

    