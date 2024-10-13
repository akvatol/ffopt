from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pymatgen.io.cif import CifParser
from pyxtal import pyxtal

from ffopt.parsers.cif import (
    ParserCif,
    gulp_only_core_structure,
    get_full_lattice,
    get_group_number,
    get_irr_atoms,
    get_lattice_type,
)

# Example CIF file path for testing
TEST_CIF_PATH = Path("test_files/NbS.cif")


def test_parser_parse():
    """Test the parse function of ParserCif using a real CIF file."""
    parser = ParserCif(TEST_CIF_PATH)
    parser.parse()

    # Check if the extracted data contains expected keys
    assert "group_number" in parser._data
    assert "lattice_type" in parser._data
    assert "lattice_par_dof" in parser._data
    assert "atoms_dof" in parser._data

    # Validate group number and lattice type
    assert parser._data["group_number"] == 194
    assert parser._data["lattice_type"] == "hexagonal"


def test_get_group_number():
    """Test the get_group_number function with a real pyxtal object."""
    # Load structure from CIF
    parser = CifParser(TEST_CIF_PATH)
    structure = parser.get_structures(primitive=True)[0]

    # Create pyxtal object
    xtal_obj = pyxtal()
    xtal_obj.from_seed(structure)

    # Check group number
    group_number = get_group_number(xtal_obj)
    assert group_number == 194


def test_get_lattice_type():
    """Test the get_lattice_type function with a real pyxtal object."""
    # Load structure from CIF
    parser = CifParser(TEST_CIF_PATH)
    structure = parser.get_structures(primitive=True)[0]

    # Create pyxtal object
    xtal_obj = pyxtal()
    xtal_obj.from_seed(structure)

    # Check lattice type
    lattice_type = get_lattice_type(xtal_obj)
    assert lattice_type == "hexagonal"


def test_get_full_lattice():
    """Test the get_full_lattice function with a real pyxtal object."""
    # Load structure from CIF
    parser = CifParser(TEST_CIF_PATH)
    structure = parser.get_structures(primitive=True)[0]

    # Create pyxtal object
    xtal_obj = pyxtal()
    xtal_obj.from_seed(structure)

    # Check full lattice parameters
    full_lattice = get_full_lattice(xtal_obj)
    expected_params = [3.32, 3.32, 6.460000, 90.0, 90.0, 120.0]
    expected_dof = [1, 0, 1, 0, 0, 0]  # For hex
    assert full_lattice == expected_params + expected_dof


def test_get_irr_atoms():
    """Test the get_irr_atoms function with a real pyxtal object."""
    # Load structure from CIF
    parser = CifParser(TEST_CIF_PATH)
    structure = parser.get_structures(primitive=True)[0]

    # Create pyxtal object
    xtal_obj = pyxtal()
    xtal_obj.from_seed(structure)

    # Get irreducible atoms
    irr_atoms = get_irr_atoms(xtal_obj)
    
    # Check that the irreducible atoms list has the correct length and content
    assert len(irr_atoms) == 2  
    assert irr_atoms[1][:4] == ["S", 1 / 3, 2 / 3, 0.2500]
    assert irr_atoms[1][4:] == [0, 0, 0]
    assert irr_atoms[0][:4] == ["Nb", 0.0000, 0.0000, 0.0000]
    assert irr_atoms[0][4:] == [0, 0, 0]


def test_gulp_only_core_structure():
    """Test the get_irr_atoms function with a real pyxtal object."""
    # Load structure from CIF
    parser = CifParser(TEST_CIF_PATH)
    structure = parser.get_structures(primitive=True)[0]

    # Create pyxtal object
    xtal_obj = pyxtal()
    xtal_obj.from_seed(structure)

    # Get irreducible atoms
    struct = gulp_only_core_structure(xtal_obj)
    
    # Check that the irreducible atoms list has the correct length and content
    assert struct == 'cell\n3.32 3.32 6.46 90.0 90.0 120.0 1 0 1 0 0 0\nfractional\nNb core 0.0 0.0 0.0 0.0 0 0 0\nS core 0.3333333333333333 0.6666666666666666 0.25 0.0 0 0 0\nspace\n194'