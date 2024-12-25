import pandas as pd
import utils


FEAT_DATA: pd.DataFrame = utils.load_feats()
ACTION_DATA: pd.DataFrame = utils.load_actions()