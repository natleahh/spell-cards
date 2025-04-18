"""Imeplements classes for querying TTRPG Records."""
from argparse import ArgumentParser
from functools import cached_property
import functools
import itertools
import json
from pathlib import Path
import sys
from typing import Literal, Self
import pandas as pd
from jsonpath_ng import JSONPath, ext

import utils

Source = Literal["dnd5etools", "pf2etools"]

class TTRPGRecords(pd.DataFrame):
    """Class for holding, querying and indexing TTRPG Record data."""

    def __init__(self, records: list[dict], index: list[str]):
        """Intilises a TTRPGRecords instance.

        Args:
            records (list[dict]): List or TTRPG Records
            index (list[str]): List of columns to index data by.
        """
        super().__init__(records, dtype="object")
        self.set_index(index, inplace=True)

    
    @classmethod
    def from_paths(cls, fs_path: Path, json_path: JSONPath, index: list[str] | None = None) -> type[Self]:
        """Procuces a TTRPGRecords instance, from file_system_path and a JSON Path.

        Args:
            fs_path (Path): Path to a directory or .json file f
            json_path (JSONPath): JSON path to TTRPGRecord data.
            index (list[str] | None, optional): List of TTRPG Record value to index by. Defaults to None.
        """
        files = cls.get_source_files(fs_path)
        records = [*itertools.chain.from_iterable(
            cls.get_records(file, json_path)
            for file in files
        )]
        return cls(records, index or ["name", "source"])

    @staticmethod
    def get_source_files(path: Path) -> list[Path]:
        """Produces a list of path to JSON files containing TTRPG Data.

        Args:
            path (Path): Path to file or directory.

        Raises:
            FileNotFoundError: If file or directory doesn't exist.
            ValueError: If non-JSON file path is provided.
        """
        if not path.exists():
            raise FileNotFoundError(f"No data source found at {path.as_posix()}")
                
        if not path.is_dir():
            if path.suffix != ".json":
                raise ValueError(f"Path {path.as_posix()} is not a .json of directory.")
            return [path]
        elif (path / "index.json").exists():
            index_data = json.loads((path / "index.json").read_text())
            return [path / file_path for file_path in index_data.values()]
        else:
            return [*path.glob("*.json")]

    @staticmethod
    def get_records(file_path: Path, json_path: JSONPath) -> dict:
        """Produces a list of TTRPG Record from the file_path and json_path provided.

        Args:
            file_path (Path): Path to a JSON file.
            json_path (JSONPath): JSON path to a list of TTRPG Records.
        """
        raw_data = json.loads(file_path.read_text())
        records = []
        for match in json_path.find(raw_data):
            records.extend(match.value)
        return records
    

    @staticmethod
    def naiive_by_sources(source: str, sources: list[str]) -> int:
        """Returns the index the source provided appear in sources provided.

        If `source is not in sources, returns max int. If no sources
        provided, returns 0. 

        Args:
            source (str): TTRPG Source.
            sources (list[str]): List of TTRPG Sources.

        """
        if not sources:
            return 0
        try:
            return sources.index(source)
        except ValueError:
            return sys.maxsize

    
    def query_record(self, name: str, sources: list[str] | None = None) -> dict:
        """Returns a record TTRPG record for the provided parameters.
        
        Args:
            name (str): Record Name.
            sources (list[str] | None, optional): List of TTRPG Sources. Defaults to None.

        """
        index_selector = [name] if sources is None else self.index.intersection(
            list(itertools.product([name], sources))
        )
        raw_query = self.loc[index_selector]
        by_source = functools.partial(self.naiive_by_sources, sources=sources or [])
        query = raw_query.sort_values(by="source", key=lambda col: col.map(by_source)).reset_index()
        return query.iloc[0].dropna().to_dict()
    
    @classmethod
    def _combine(cls, a: Self, b: Self) -> Self:
        """Combines two TRRPG records into one."""
        if a.index.names != b.index.names:
            raise ValueError("Indexes of provided TTRPGRecords do not match.")
        records = [
            *a.reset_index().to_dict("records"),
            *b.reset_index().to_dict("records")
        ]
        return cls(records, index=a.index.names)
    
    @classmethod
    def combine(cls, ttrpg_records: list[Self]):
        """Combines a list of TTRPGRecords into a single record.

        Args:
            ttrpg_records (list[Self]): List of TTRPG Records
        """
        return functools.reduce(cls._combine, ttrpg_records)



    def _get_data_summary(self) -> dict:
        """Retrieve a summary of all entries within this Record source, sorted by type."""
        entries = itertools.chain(*itertools.chain(*map(self._extract_entries, self["entries"])))
        by_entry_type = lambda e: "txt" if isinstance(e, str) else e["type"]
        return dict(
            (name, list(data))
            for name, data in
            itertools.groupby(sorted(entries, key=by_entry_type), key=by_entry_type)
        )
    
    @staticmethod
    def _extract_entries(entry) -> str | dict:
        """Utility function for recurrisvely extracting entries from TTRPG Records."""
        entries = [entry]
        if isinstance(entry, dict) and "entries" in entry:
            for sub_entry in entry["entries"]:
                entries.extend(TTRPGRecords._extract_entries(sub_entry))
        return entries



        
class TTRPGData(Path):

    def __init__(self, source_dir: str):
        """Initialises a TTRPG Data Source.

        Args:
            source_dir (str): Source Directory containing TTRPG Data.

        Raises:
            FileNotFoundError: If no such directory exists.
            ValueError: If file system location is not a directory.
        """
        super().__init__(source_dir)
        if not self.exists():
            raise FileNotFoundError()
        if not self.is_dir():
            raise ValueError()

    def _fetch_records(self, fs_path: str, json_path: str) -> TTRPGRecords:
        """Fetches TTRPG Record Data from the filesystem and JSON path."""
        return TTRPGRecords.from_paths(fs_path=Path(self) / fs_path, json_path=ext.parse(json_path))


class Dnd5eToolsData(TTRPGData):


    @cached_property
    def spells(self):
        """:TTRPGRecords: DnD 5e Spell Data."""
        return self._fetch_records("data/spells/", "$.spell")
    
    @cached_property
    def monsters(self):
        """:TTRPGRecords: DnD 5e Monster Data."""
        return self._fetch_records("data/beastiary/", "$.monster")

    @cached_property
    def class_features(self):
        """:TTRPGRecords: DnD 5e Class Feature Data."""
        return self._fetch_records("data/class/", "$.classFeature|subclassFeature")

    @cached_property
    def feats(self):
        """:TTRPGRecords: DnD 5e Feat Data."""
        return self._fetch_records("data/feats.json", "$.feat")


class PF2eToolsData(TTRPGData):

    @cached_property
    def feats(self):
        """:TTRPGRecords: Pathfinder 2e Feat Data."""
        return self._fetch_records("data/feats/" "$.feat")


    @cached_property
    def actions(self):
        """:TTRPGRecords: Pathfinder 2e Action Data."""
        return self._fetch_records("data/actions.json", "$.action")
    
    @cached_property
    def spells(self) -> TTRPGRecords:
        """:TTRPGRecords: Pathfinder 2e Spell Data."""
        return self._fetch_records("data/spells/", "$.spell")


def main(argv: None | list[str] = None):
    """Command Line Interface for retreiving entry data."""
    parser = ArgumentParser(
        prog="data_auditor",
        description="Exports a JSON summary of Entry Data."
    )
    parser.add_argument("system_source", choices=["dnd5e", "pf2e"])
    parser.add_argument("record_type")

    args = parser.parse_args(argv)
    if args.system_source == "dnd5e":
        data_source = Dnd5eToolsData(utils.get_env_variable("DND_DATA_PATH"))
    else:
        data_source = PF2eToolsData(utils.get_env_variable("PATHFINDER_DATA_PATH"))
    records  = getattr(data_source, args.record_type)
    print(json.dumps(TTRPGRecords._get_data_summary(records), indent=4))

    
if __name__ == "__main__":
    main()

