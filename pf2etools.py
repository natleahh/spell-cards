from typing import Literal, Optional, TypedDict

import pandas as pd

import sources
import utils


class BaseDict(TypedDict):
    
    @classmethod
    def from_raw_dict(cls, data):
        filtered_data = {
            k: v.from_raw_dict() if "from_raw_dict" in type(v).__dict__ else v
            for k, v 
            in data.items() if k in cls.__annotations__
        }
        
        return cls(filtered_data)
    
    

class SearchableElement(BaseDict):
    
    @classmethod
    def from_name(cls, name: str, source: str, data_source: pd.DataFrame):
        df_index = (name,) if source is None else (name, source)
        return cls.from_raw_dict(data_source.loc[df_index])
        
        
class Activity(BaseDict):
    number: Optional[int]
    unit: Literal["free", "action", "reaction", "bonus action"]


class Action(SearchableElement):
    name: str
    traits: list[str]
    activity: Activity
    trigger: Optional[str]
    entries: list[str | dict]
    
    @classmethod
    def from_name(cls, name, source: str = "CRB"):
        return SearchableElement.from_name(name=name, source=source, data_source=sources.ACTION_DATA)
    



class Feat(SearchableElement):
    name: str
    traits: list[str]
    entries: list[str | dict]
    
    @classmethod
    def from_name(cls, name, source: str = "CRB"):
        return SearchableElement.from_name(name=name, source=source, data_source=utils.load_feats())
    
    
if __name__ == "__main__":
    import pathbuilder
    build = pathbuilder.Build.from_json_id(182206)
    feats = list(map(Feat.from_name, build["feats"]))
    pass
    