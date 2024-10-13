from pathlib import PurePath


class BaseParser:
    """Extendable parser for gulp out files."""

    def __init__(self, filepath: PurePath):
        self.filepath = filepath
        self._data: dict = {}
        self.__extractors: dict = {}

    def parse(self) -> None:
        with open(self.filepath, 'r') as file:
            content = file.read()

        for key, extractor in self.__extractors.items():
            self._data[key] = extractor(content)

    @property
    def extractors(self):
        return self.__extractors

    @extractors.setter
    def extractors(self, key: str, extractor) -> None:
        self.__extractors[key] = extractor

    def pop_extractor(self, key: str) -> None:
        self.__extractors.pop(key, None)

    @property
    def data(self) -> dict:
        return self._data
