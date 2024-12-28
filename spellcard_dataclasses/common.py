from typing import TypedDict


class StructCommon(dict):
    STRUCTURE: type[TypedDict] = TypedDict
        
    @classmethod
    def from_raw_dict(cls, raw_dict):
        return cls(cls.STRUCTURE(raw_dict))