import tomllib
from pathlib import Path

from pymatgen.core import Lattice
from pymatgen.core import Structure as PmgStructure
from pyxtal import pyxtal

from ffopt.parsers.cif import ParserCif


class TomlFileReader:
    """
    A class for reading and loading data from a TOML file.

    Attributes:
        file_path (Path): Path to the TOML file to be read.
        data (dict or None): Stores the loaded TOML data after reading.
    """

    def __init__(self, file_path: str):
        """
        Initialize the TomlFileReader with the path to a TOML file.

        Args:
            file_path (str): The path to the TOML file to be read.
        """
        self.file_path = Path(file_path)
        self.data = None

    def read(self) -> dict:
        """
        Reads and returns the data from the TOML file.

        Returns:
            dict: Parsed data from the TOML file.
        """
        if self.data is None:
            with open(self.file_path, "rb") as f:
                self.data = tomllib.load(f)
        return self.data


class StructureHandler:
    """
    A class for handling and processing structural data from a dictionary.

    Attributes:
        data (dict): Input data containing model and structure information.
        structures_data (dict): Extracted structure data from the input data.
        processed_structures (dict): Stores processed structural information.
    """

    def __init__(self, data: dict):
        """
        Initialize the StructureHandler with input data and extract structures.

        Args:
            data (dict): A dictionary containing structure information under the key 'model' -> 'structures'.
        """
        self.data = data
        self.structures_data = data.get("model", {}).get("structures", {})
        self.processed_structures = {}

    def process_structures(self):
        """
        Processes each structure entry in `structures_data`.

        For each structure, determines if it is a CIF file or a custom structure
        and processes it accordingly. Updates the structure information with
        lattice parameters (`cell`) and atomic coordinates (`atoms`), then saves
        this in `processed_structures`.

        Finalizes by updating `self.data` with the processed structures.
        """
        for name, struct_info in self.structures_data.items():
            structure_content = struct_info.get("structure", "").strip()

            pyxtal_structure = (
                self._read_structure_from_cif(structure_content)
                if structure_content.endswith(".cif")
                else self._parse_custom_structure(structure_content)
            )

            data = ParserCif(content=pyxtal_structure)
            data.parse()
            # Нужно для того чтобы можно было сравнивать посчитанные результаты
            # т.к. калькулятор погрешностей учитывает какие параметры структуры
            # оптимизировались
            struct_info.update({
                "cell": data.data["lattice_par_dof"],
                "atoms": data.data["atoms_dof"],
            })
            self.processed_structures[name] = struct_info

        # Update the original data structure with processed structures
        self.data["model"]["structures"] = self.processed_structures

    def _read_structure_from_cif(self, file_path: str) -> pyxtal:
        """
        Reads structural data from a CIF file and converts it to a pyxtal object.

        Args:
            file_path (str): Path to the CIF file.

        Returns:
            pyxtal: The structure as a pyxtal object for further processing.
        """
        pmg_structure = PmgStructure.from_file(file_path)
        pyxtal_structure = pyxtal()
        pyxtal_structure.from_seed(pmg_structure)
        return pyxtal_structure

    def _parse_custom_structure(self, structure_str: str) -> pyxtal:
        """
        Parses a custom structure string format into a pyxtal object.

        Args:
            structure_str (str): The custom structure string to be parsed.

        Returns:
            pyxtal: A pyxtal object initialized with the parsed structural information.

        Processing details:
            - Extracts lattice parameters from the 'cell' line.
            - Reads atomic species and coordinates, distinguishing between fractional
              and Cartesian coordinates based on 'frac' or 'cart' keywords.
            - Constructs a pymatgen Structure object with this data, and initializes a
              pyxtal structure from it.
        """
        lines = structure_str.strip().splitlines()
        lattice_params, species, coords = None, [], []
        coords_are_frac = False
        atoms = False

        for n, line in enumerate(lines):
            line = line.strip()
            if line.startswith("cell"):
                lattice_params = [float(x) for x in lines[n + 1].split()[:6]]
            elif line.startswith(("frac", "cart")):
                coords_are_frac = line.startswith("frac")
                # XXX
                atoms = True
            elif line.startswith("space"):
                _sg = int(lines[n + 1].strip())
            elif line and not line.startswith("#") and atoms:
                tokens = line.split()
                if len(tokens) >= 4:
                    species.append(tokens[0])
                    coords.append([float(tokens[i]) for i in range(1, 4)])

        lattice = Lattice.from_parameters(*lattice_params)
        pmg_structure = PmgStructure(
            lattice, species, coords, coords_are_cartesian=not coords_are_frac
        )
        pyxtal_structure = pyxtal()
        pyxtal_structure.from_seed(pmg_structure)
        return pyxtal_structure


class DataPreparer:
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.data = None

    def prepare_data(self) -> dict:
        """Prepare and process the data read from the TOML file."""
        reader = TomlFileReader(self.input_file)
        self.data = reader.read()

        structure_handler = StructureHandler(self.data)
        structure_handler.process_structures()

        return self.data
