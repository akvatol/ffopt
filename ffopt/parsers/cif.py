"""Interface to GULP, the General Utility Lattice Program."""

from pathlib import PurePath

from pymatgen.io.cif import CifParser
from pyxtal import pyxtal

from ffopt.parsers.base import BaseParser

__all__ = ['ParserCif', ] 


class ParserCif(BaseParser):
    """
    Instance of BaseParser with some extra extraction functions typically
    used when processing .out files.
    """

    def __init__(self, filepath: PurePath):
        super().__init__(filepath)
        self.__extractors = {
            "group_number": get_group_number,
            "lattice_type": get_lattice_type,
            "lattice_par_dof": get_full_lattice,
            "atoms_dof": get_irr_atoms,
            # to get GULP formated structure repr
            "gulp_only_core_structure": gulp_only_core_structure,
        }

    def parse(self) -> None:
        # TODO: Проверка на работу со сломанным парсером/mmcif
        xtal_obj = pyxtal()
        parser = CifParser(self.filepath)
        structure = parser.parse_structures(primitive=True)[0]
        xtal_obj.from_seed(structure)

        for key, extractor in self.__extractors.items():
            self._data[key] = extractor(xtal_obj)


def get_group_number(pyxtal_obj):
    return pyxtal_obj.group.number


def get_lattice_type(pyxtal_obj):
    return pyxtal_obj.group.lattice_type


def get_lattice_params(pyxtal_obj):
    params = pyxtal_obj.lattice.get_para(degree=True)
    return [round(i, 4) for i in params]


def get_lattice_dof(pyxtal_obj):
    match pyxtal_obj.group.lattice_type:
        case "triclinic":
            return [1] * 6
        case "monoclinic":
            return [1, 1, 1, 0, 1, 0]
        case "orthorhombic":
            return [1, 1, 1, 0, 0, 0]
        case "trigonal" | "hexagonal":
            return [1, 0, 1, 0, 0, 0]
        case "cubic":
            return [1, 0, 0, 0, 0, 0]


def get_full_lattice(pyxtal_obj):
    return [*get_lattice_params(pyxtal_obj),
            *get_lattice_dof(pyxtal_obj)]


def get_irr_atoms(pyxtal_obj):
    atoms = []
    for atom in pyxtal_obj.atom_sites:
        symb = atom.specie
        pos = atom.position
        dof = _dof_to_opt(atom.wp.get_frozen_axis())
        atoms.append([symb, *pos, *dof])
    return atoms


def _dof_to_opt(dofs: list):
    opt = [1, 1, 1]

    if not dofs:
        return opt

    for dof in dofs:
        opt[dof] = 0

    return opt


def _convert_coordinates_to_gulp_core_only(atoms: list) -> str:
    new_data = []
    for atom in atoms:
        atom.insert(1, "core")
        atom.insert(5, 0.0)
        new_data.append(" ".join(str(i) for i in atom))
    return "\n".join(new_data)


def _convert_coordinates_to_gulp_core_and_shell(atoms: list) -> str:
    new_data = []
    for atom in atoms:
        for idx in ["core", "shell"]:
            _atom = atom.copy()
            _atom.insert(1, idx)
            _atom.insert(5, 0.0)
            new_data.append(_atom)
    return "\n".join(new_data)


def gulp_only_core_structure(pyxtal_obj):
    # Gulp-file structure format:
    # cell - scince we work with ciff
    # a b c alpha betta gamma ? ? ? ? ? ? - where ? = 1 or 0
    # fractional | cartesian (we use frac coord system)
    # Atmon core|shell a b c 0.0 ? ? ?
    # space
    # spacegroup number
    structure = f"""cell
{' '.join(str(i) for i in get_full_lattice(pyxtal_obj))}
fractional
{_convert_coordinates_to_gulp_core_only(get_irr_atoms(pyxtal_obj))}
space
{get_group_number(pyxtal_obj)}"""
    return structure
