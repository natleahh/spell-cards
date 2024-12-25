
from functools import cache
import json
from pathlib import Path

import numpy as np
import pandas as pd

import static
     
def get_data_path():
    path = Path(static.DATA_PATH)
    if not path.exists():
        raise FileNotFoundError(f"DATA_PATH: {path} does not exist.")
    return path

def get_feats_index():
    with (get_data_path() / "feats/index.json").open() as index_file:
        return json.load(index_file)

def prepare_df(df: pd.DataFrame):
    return df.set_index(["name", "source", df.index]).replace(float("nan"), None)

@cache
def load_feats():
    data_path =  get_data_path()
    feat_path = data_path / "feats"
    index_data = get_feats_index()
    all_feats = [
        feat 
        for source in static.SOURCES
        for feat in json.loads((feat_path / index_data[source]).read_text())["feat"]
    ]
    for class_path in (data_path / "class").glob("*"):
        for class_feature in json.loads(class_path.read_text()).get("classFeature", []):
            all_feats.append(class_feature)
    
    for ancestry_path in (data_path / "ancestries").glob("*"):
        for ancestry_data in json.loads(ancestry_path.read_text()).get("ancestry", []):
            all_feats.extend(ancestry_data.get("features", []))
            all_feats.extend(ancestry_data["heritage"])            
            for heritage_data in ancestry_data["heritage"]:
                for entry in heritage_data["entries"]:
                    if not isinstance(entry, dict):
                        continue
                    all_feats.append(entry)
    base_df = pd.DataFrame(all_feats).replace({np.nan: None})
       
    return prepare_df(base_df)


@cache
def load_actions():
    action_data = json.loads((get_data_path() / "actions.json").read_text())
    base_df =  pd.DataFrame(action_data["action"])
    return prepare_df(base_df)

    
    
        