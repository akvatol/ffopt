import tomllib
from pathlib import Path
import click
from pymatgen.core import Structure as PmgStructure, Lattice
from pyxtal import pyxtal

class TomlFileReader:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data = None

    def read(self) -> dict:
        with open(self.file_path, 'rb') as f:
            self.data = tomllib.load(f)
        return self.data

class StructureHandler:
    def __init__(self, data: dict):
        self.data = data
        self.structures_data = data.get('model', {}).get('structures', {})
        self.processed_structures = {}

    def process_structures(self):
        for name, struct_info in self.structures_data.items():
            structure_content = struct_info.get('structure', None) #обращение к ключу структуры 

            if structure_content.strip().endswith('.cif'): #проверка является ли это cif
                structure_path = Path(structure_content.strip())
                pyxtal_structure = self._read_structure_from_cif(str(structure_path))
            else:
                pyxtal_structure = self._parse_custom_structure(structure_content) #иначе работа со строкой

            struct_info['pyxtal_structure'] = pyxtal_structure
            self.processed_structures[name] = struct_info

        self.data['model']['structures'] = self.processed_structures

    def _read_structure_from_cif(self, file_path: str) -> pyxtal:
        pmg_structure = PmgStructure.from_file(file_path)
        pyxtal_structure = pyxtal()
        pyxtal_structure.from_seed(pmg_structure)
        return pyxtal_structure

    def _parse_custom_structure(self, structure_str: str) -> pyxtal:
        lines = structure_str.strip().split('\n')
        lattice_params = None
        species = []
        coords = []
        coords_are_frac = False

        for line in lines:
            line = line.strip()
            if line.startswith('cell'):
                parts = line.split()
                lattice_params = [float(x) for x in parts[1:7]]
            elif line.startswith('frac'):
                coords_are_frac = True
            elif line.startswith('space'):
                # Пространственная группа
                pass
            elif line and not line.startswith('#'):
                tokens = line.split()
                if len(tokens) >= 4:
                    species.append(tokens[0])
                    coords.append([float(tokens[1]), float(tokens[2]), float(tokens[3])])

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
        reader = TomlFileReader(self.input_file)
        self.data = reader.read()

        structure_handler = StructureHandler(self.data)
        structure_handler.process_structures()

        self.data = structure_handler.data

        return self.data
