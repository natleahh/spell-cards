from itertools import starmap
import re

from spellcard_structs.card import RPGCard
from spellcard_dataclasses import dnd5etools, dndbeyond, pathbuilder, pf2etools
import utils.sources as sources

class CardFactor(list):

    CARD_DIM = (45, 20)
    
    def format_list_items(self, items: list[dict]):
        for item in items:
            for i, entry in enumerate(item['entries']):
                if i == 0:
                    yield f"bullet | {item['name']}: {entry}"
                else:
                    yield f"text | {entry}"

    def get_block_size(self, line: str):
        tabbed_padding = 0
        end_padding = 0
        line_length = 0
        content = line.split(" | ")[-1]
        match line.split(" | "):
            case ["rule" | "ruler"]:
                return 1.0
            case ["property", property_name, text_body]:
                content = f"{property_name} {text_body}"
                tabbed_padding = 2
            case ["text", _]:
                end_padding = 1
            case ["bullet", _]:
                line_length = 4
                tabbed_padding = 4
            case [_, _]:
                pass
            case unhandled:
                raise ValueError(f"Unhandled case {unhandled}")
        size = 0
        for word in content.split(" "):
            word_length = len(word) + 1
            if line_length + word_length > self.CARD_DIM[0]:
                size += 1
                line_length = tabbed_padding
            line_length += word_length
        return size + end_padding + (line_length / self.CARD_DIM[0])


    def split_content(self, content: list[str], header_size: int, max_size: int):
        line_count = header_size
        sublists = [[]]
        while content:
            line = content.pop(0)
            block_size = self.get_block_size(line=line)
            if block_size + line_count > max_size:
                *head, text = line.split(" | ")
                line_overspill = max_size - (block_size + line_count)
                char_overspill = int(line_overspill * self.CARD_DIM[0]) - len("(cont.)")
                try:
                    while line[char_overspill] != " ":
                        char_overspill -= 1
                except IndexError:
                    char_overspill = 0
                front, back = text[:char_overspill], text[char_overspill:]
                if front:
                    sublists[-1].append(f"{' | '.join([*head, front])} (cont.)")
                line_count = header_size
                if back:
                    content.insert(0, f"{' | '.join([*head, '(cont.) ' + back])}")
                sublists.append([])
            else:
                sublists[-1].append(line)
                line_count += int(block_size)
        
        return [*filter(bool, sublists)]

class Dnd5eSpells(CardFactor):

    @classmethod
    def from_spell_names(cls, spell_names: list[str]):
        return cls(map(dnd5etools.Spell.from_name, spell_names))
    
    @classmethod
    def from_dndbeyond_build(cls, build: dndbeyond.Build):
        return cls(map(dnd5etools.Spell.from_name, build.all_spell_names))
    
    @classmethod
    def from_dndbeyond_id(cls, id: int):
        return cls.from_dndbeyond_build(dndbeyond.Build.from_json_id(id))
    
    def get_text_body(self, spell: dnd5etools.Spell):        
        traits = [
            "subtitle | {} {}".format(spell.get_spell_level().capitalize(), spell.get_school().capitalize()),
            "rule"
        ]
        
        for property, details in spell.get_header_data().items():
            if details is None:
                continue
            traits.append(f"property | {property} | {details}")
            
        traits.append("rule")
        
        content = []
        
        for entry in spell["entries"]:
            if isinstance(entry, str):
                content.append(f"text | {entry}")
            # elif entry["type"] == "successDegree":
            #     content.extend(starmap("property | {} | {}".format, entry["entries"].items()))
            elif entry["type"] == "list":
                content.extend(map("bullet | {}".format, entry["items"]))
            elif entry["type"] == "entries":
                a, *b = entry["entries"]
                content.append(f"property | {entry['name']} | {a}")
                content.extend(map("text | {}".format, b))
            elif entry["type"] == "table":
                for rows in [entry['colLabels'], *entry['rows']]:
                    content.append(" | ".join(["bullet", *rows]))
            else:
                raise ValueError(f"{spell['name']} has unsupported entry")
        content = [
            re.sub(r"{\@\w+ ([\w\s]*\|){0,2}?([\w\s]+)(\|[A-Z0-9]{2,4})?}", r"\g<2>", entry)
            for entry in content
        ]
        
        sub_lists = self.split_content(
            content=content,
            header_size=sum(map(self.get_block_size, traits)) + 4,
            max_size=self.CARD_DIM[1]
            )
        return [[*traits, *sub_list] for sub_list in sub_lists]
        
    
    def get_card_from_spell(self, spell: dnd5etools.Spell): 
        icon = "white-book-{}".format(spell["level"])
        contents = self.get_text_body(spell)
        cards = []
        for i, content in enumerate(contents, 1):
            title = "{}{}".format(
                spell["name"],
                f" ({i}/{len(contents)})" if len(contents) > 1 else  ""
            )
            card = RPGCard(
                title=title,
                count=1,
                color="Chocolate",
                icon=icon,
                icon_back="",
                contents=content,
                tags=[]
            )
            
            cards.append(card)
        return cards
    
    def get_all_cards(self):
        return [
            card
            for spell in self
            for card in self.get_card_from_spell(spell)
        ]

class PathFinderActions(CardFactor):
    
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
        sub_lists = self.split_content(content, 45)
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
