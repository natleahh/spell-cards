import pandas as pd
import utils


FEAT_DATA: pd.DataFrame = utils.load_feats()
ACTION_DATA: pd.DataFrame = utils.load_actions()
BONUS_BY_PROFICIENCY = dict((name, i * 2)  for i, name in enumerate(utils.static.PROFICIENCY_LEVELS))
PROFICIENCY_BY_BONUS = dict(map(reversed, BONUS_BY_PROFICIENCY.items()))