
from functools import cache
import json
import os
from pathlib import Path

import pandas as pd

import static
     
def get_data_path():
    path = Path(static.DATA_PATH)
    if not path.exists():
        raise FileNotFoundError("DATA_PATH: {path} does not exist.")
    return path

def get_feats_index():
    with (get_data_path() / "feats/index.json").open() as index_file:
        return json.load(index_file)
    

@cache
def load_feats():
    data_path =  get_data_path()
    feat_path = data_path / "feats"
    index_data = get_feats_index()
    feats = {}
    for source in static.SOURCES:
        source_data = json.loads((feat_path / index_data[source]).read_text())
        mapped = {(v["name"], v["source"]): v for v in source_data["feat"]}
        feats |= mapped
    
    # for class_path in (data_path / "class").glob("*"):
    #     for class_feature in json.loads(class_path.read_text())["classFeature"]:
    #         feats[(class_feature["name"], class_feature["source"])] = class_feature
       
    return pd.DataFrame(feats)


@cache
def load_actions():
    action_data = json.loads((get_data_path() / "actions.json").read_text())
    mapped_actions = {(action["name"], action["source"]): action for action in action_data["action"]}
    return pd.DataFrame(mapped_actions)

    
    
        