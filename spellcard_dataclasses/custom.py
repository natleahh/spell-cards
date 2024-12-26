from itertools import starmap
import re

from spellcard_structs.card import RPGCard
from spellcard_dataclasses import pathbuilder, pf2etools
import utils.sources as sources

class CardFactor(list):
    
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


class PathFinderActions(list[pf2etools.Action]):
    
    @classmethod
    def from_pathbuilder_build(cls, build: pathbuilder.Build):
        feat_action = cls.actions_from_feat_names(cls=cls, feat_names=pathbuilder.Build.get_all_feat_names(build))
        basic_actions = cls.actions_from_proficiencies(
                cls=cls,
                proficiency_levels=pathbuilder.Build.get_proficiency_map(build),
        )
        
        return cls(
            pf2etools.Action.get_unique([*feat_action, *basic_actions])
        )
    
    def actions_from_feat_names(cls, feat_names: list[str]):
        actions = []
        for feat_name in feat_names:
            feat_data = pf2etools.Feat.from_name(feat_name)
            if feat_data is None:
                continue
            actions.extend(pf2etools.Feat.get_all_actions(feat_data))
        return actions
    
    def actions_from_proficiencies(cls, proficiency_levels: dict[str, str]):        
        actions = []
        for (name, source, _), action in sources.ACTION_DATA.iterrows():
            required_skills = (action.get("actionType") or {}).get("skill", {})
            proficient = True
            skill_pairs = ((level, skill) for level, skills in required_skills.items() for skill in skills)
            
            proficient = set()
            
            for level, skill in skill_pairs:
                char_prof = sources.BONUS_BY_PROFICIENCY[proficiency_levels[skill]]
                req_pro = sources.BONUS_BY_PROFICIENCY[level]
                if char_prof < req_pro:
                    proficient = set()
                    break
                proficient.add(level)
                
            if not proficient or proficient == {"untrained"}:
                continue

            actions.append(pf2etools.Action.from_name(name=name, source=source))
        return actions
            

    @classmethod
    def from_pathbuilder_json_id(cls, json_id: int):
        return cls.from_pathbuilder_build(pathbuilder.Build.from_json_id(json_id))
    
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
            case unhandled:
                raise ValueError(f"unhadled case: {unhandled} icon for {action['name']}")
    
    
    def get_text_body(self, action: pf2etools.Action):        
        traits = []
        content = []
        
        for trait in (action["traits"] or []):
            traits.append(f"p2e_trait | common | {trait}")
        
        if action["traits"]:
            traits.insert(0, "p2e_start_trait_section")
            traits.append("p2e_end_trait_section")
            traits.append("ruler")
        
        if action.get("requirements"):
            content.append(f"property | Requirements | {action['requirements']}")
        
        for entry in action["entries"]:
            if isinstance(entry, str):
                content.append(f"text | {entry}")
            elif entry["type"] == "successDegree":
                content.extend(starmap("property | {} | {}".format, entry["entries"].items()))
            elif entry["type"] == "list":
                content.extend(self.format_list_items(entry["items"]))
            elif entry["type"] == "ability":
                return self.get_text_body(pf2etools.Action.from_raw_dict(entry))
            else:
                raise ValueError(f"{action['name']} has unsupported entry")
        content = [
            re.sub(r"{\@\w+ ([\w\s]*\|){0,2}?([\w\s]+)(\|[A-Z0-9]{2,4})?}", r"\g<2>", entry)
            for entry in content
        ]
        sub_lists = self.split_content(content)
        return [[*traits, *sub_list] for sub_list in sub_lists]
            

    def get_card_from_action(self, action: pf2etools.Action):
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
        return self.get_card_from_action(action=pf2etools.Action.from_name(action_name))
    
    def get_all_cards(self):
        return [
            card
            for action in self
            for card in self.get_card_from_action(action)
        ]
