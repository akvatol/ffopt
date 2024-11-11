from pathlib import PurePath


class BaseParser:
    """Extendable parser for gulp out files."""

    def __init__(self, filepath: PurePath = None, content=None):
        self.filepath = filepath
        self._data: dict = {}
        self._extractors: dict = {}

        if filepath:
            with open(self.filepath, 'r') as file:
                self.content = file.readlines()
        else:
            self.content = content

    def parse(self) -> None:
        for key, extractor in self._extractors.items():
            self._data[key] = extractor(self.content)

    @property
    def extractors(self):
        return self._extractors

    @extractors.setter
    def extractors(self, key: str, extractor) -> None:
        self._extractors[key] = extractor

    def pop_extractor(self, key: str) -> None:
        self._extractors.pop(key, None)

    @property
    def data(self) -> dict:
        return self._data