
from dataclasses import dataclass
from itertools import starmap
import re

import pandas as pd
import webcolors

from card import RPGCard
from pathbuilder import Build
from pf2etools import Feat, Action
import sources
import static


PROFICIENCY_NAMES = [
    *static.BASE_PROFICIENCY_MAP.keys(),
    *map(str.capitalize, static.BASE_PROFICIENCY_MAP.keys())
]
PROFICIENCY_RESTRICTION_FORMAT = r"({})(.*({}).*)+".format(
    "|".join(map("({})".format, PROFICIENCY_NAMES)),
    "{}"
)


@dataclass
class CharacterData:

    actions: list[Action]
    
    @classmethod
    def from_pathbuilder_build(cls, build: Build):
        actions = []
        for feat_name in Build.get_all_feat_names(build):
            feat_data = Feat.from_name(feat_name)
            if feat_data is None:
                continue
            actions.extend(Feat.get_all_actions(feat_data))
        
        proficiency_names = [
            *build["proficiencies"],
            *map(str.capitalize, build["proficiencies"])
        ]
        pattern = PROFICIENCY_RESTRICTION_FORMAT.format(
            "|".join(map("({})".format, proficiency_names))
        )
        for (name, source, _), action in sources.ACTION_DATA.iterrows():
            result = re.search(pattern, action.get("requirements") or "")
            if result is None:
                continue
            proficiency, skill = result.group(1, 13)
            build_level = build["proficiencies"][skill.lower()] - build["level"]
            requred_level = static.BASE_PROFICIENCY_MAP[proficiency.lower()]
            if build_level < requred_level:
                continue
            Action.from_name(name=name, source=source)

        return cls(
            actions=Action.get_unique(actions)
        )
    
    @classmethod
    def from_pathbuilder_json_id(cls, json_id: int):
        return cls.from_pathbuilder_build(Build.from_json_id(json_id))
    
    @staticmethod
    def get_icon(action):
        action_format = "p2e-{}"
        match action.get("activity", {}):
            case None:
                return None
            case {"unit": "action", "number": n}:
                action_format = action_format.format("{}-action{}")
                return action_format.format(n, "s" if n > 1 else "")
            case {"unit": "reaction"}:
                return action_format.format("reaction")
            case {"unit": "free"}:
                return action_format.format("free-action")
    
    def format_list_items(self, items: list[dict]):
        for item in items:
            for i, entry in enumerate(item['entries']):
                if i == 0:
                    yield f"bullet | {item['name']}: {entry}"
                else:
                    yield f"text | {entry}"
                    
    def split_content(self, content: list[str]):
        line_count = 0
        sublists = [[]]
        
        for line in content:
            sub_line_count = len(line.split(" | ")[-1]) // 45
            line_count += sub_line_count + 2
            if line_count > 20:
                sublists[-1].append("text | cont.")
                line_count = 0
                sublists.append(["text | cont."])
            sublists[-1].append(line)
        
        return [*filter(bool, sublists)]
    
    
    def get_text_body(self, action: Action):        
        traits = []
        content = []
        
        for trait in (action["traits"] or []):
            traits.append(f"p2e_trait | common | {trait}")
        
        if action["traits"]:
            traits.insert(0, "p2e_start_trait_section")
            traits.append("p2e_end_trait_section")
            traits.append("ruler")
        
        if action["requirements"]:
            content.append(f"property | Requirements | {action['requirements']}")
        
        for entry in action["entries"]:
            if isinstance(entry, str):
                content.append(f"text | {entry}")
            elif entry["type"] == "successDegree":
                content.extend(starmap("property | {} | {}".format, entry["entries"].items()))
            elif entry["type"] == "list":
                content.extend(self.format_list_items(entry["items"]))
            else:
                raise ValueError(f"{action['name']} has unsupported entry")
        content = [
            re.sub(r"{\@\w+ ([\w\s]*\|){0,2}?([\w\s]+)(\|[A-Z0-9]{2,4})?}", r"\g<2>", entry)
            for entry in content
        ]
        sub_lists = self.split_content(content)
        return [[*traits, *sub_list] for sub_list in sub_lists]
            

    def get_card_from_action(self, action: Action):
        icon = self.get_icon(action)
        contents = self.get_text_body(action)
        cards = []
        for i, content in enumerate(contents, 1):
            title = "{}{}".format(
                action["name"],
                f" ({i}/{len(contents)})" if len(contents) > 1 else  ""
            )
            card = RPGCard(
                title=title,
                count=1,
                color="Chocolate",
                icon=icon,
                icon_back="",
                contents=content,
                tags=action["traits"]
            )
            
            cards.append(card)
        return cards
    
    def get_card_from_action_name(self, action_name):
        return self.get_card_from_action(action=Action.from_name(action_name))
    
    
    def get_all_cards(self):
        return [
            card
            for action in self.actions
            for card in self.get_card_from_action(action)
        ]
