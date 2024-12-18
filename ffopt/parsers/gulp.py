import re
from functools import partial

from pymatgen.core import Element, Lattice, Structure
from pyxtal import pyxtal

from ffopt.parsers.base import BaseParser


class GulpSParser(BaseParser):
    """A parser for GULP `.out` files containing data for a single system."""

    def __init__(self, filepath, content=None):
        super().__init__(filepath, content)
        self._extractors = {
            "atoms": read_asymmetric_unit,
            "cell": read_cell_parameters,
            "energy": read_energy,
            "structure": parse_to_pyxtal,
            "bulk_modulus": partial(
                read_bulk_shear, pattern="Bulk  Modulus (GPa)"
            ),
            "shear_modulus": partial(
                read_bulk_shear, pattern="Shear Modulus (GPa)"
            ),
            "young_modulus": partial(
                read_bulk_shear, pattern="Youngs Moduli (GPa)"
            ),
            "elastic_values": parse_elastic_constant_matrix,
            # "phonon_gamma": read_phonon_G,
            "kpoints_values": read_phonon_kpoints,
        }


def read_phonon_kpoints(content):
    regex = r"Frequencies \(cm-1\) \[NB: Negative implies an imaginary mode\]:\s+((?:\-*\d+\.\d+\s+)+)"
    data = []
    content = "\n".join(content)
    # Use re.DOTALL to ensure the dot matches newline characters
    res = re.findall(regex, content, re.DOTALL)
    if res:
        for match in res:
            x = match.strip().split()
            data.append([float(j) for j in x])
    else:
        data = [-1000]
    return data


def read_cell_parameters(content):
    """
    Parse the final cell parameters from the given text content.

    Parameters:
    content (list of str): The lines of the text file or content.

    Returns:
    dict: A dictionary with cell parameters, where each key is the parameter
          (e.g., 'a', 'b', 'c', 'alpha', etc.), and each value is a dictionary
          containing 'value' and 'unit'.
    """
    cell_parameters = []

    # Regular expression to match lines with cell parameters
    pattern = re.compile(r"\s*(\w+)\s+([\d\.]+)\s+(\w+)")
    parsing = False
    match = None

    for line in content:
        if "Final cell parameters and derivatives" in line:
            parsing = True
            continue

        # TODO: Change the way it work
        if "Primitive cell volume" in line:
            break

        if parsing:
            match = pattern.match(line)

        if match:
            _param, value, _unit = match.groups()
            cell_parameters.append(float(value))

    return cell_parameters


def read_phonon_G(content):
    """
    Read phonon frequencies at the Gamma point from a completed GULP job.

    Parameters:
    content (list): A list of lines representing the output from the GULP job.
    n (int): The number of frequencies to read.

    Returns:
    list: A list of phonons (floats)
    """
    freq = []
    try:
        i = (
            content.index(
                "  Frequencies (cm-1) \
[NB: Negative implies an imaginary mode]:\n"
            )
            + 2
        )
    except ValueError:
        return [-1000]

    while i < len(content):
        line = content[i].strip()

        if "--------" in line or not line:
            break
        try:
            freq.extend(map(float, line.split()))
        except ValueError:
            return [-1000]

        i += 1

    # Ensure we return exactly `n` frequencies
    return freq if len(freq) >= 1 else [-1000]


def read_asymmetric_unit(content):
    """
    Parse the asymmetric unit coordinates from the given text content.

    Parameters:
    content (list of str): The lines of the text file or content.

    Returns:
    list of dict: A list of dictionaries, each representing an atom with
                  'no', 'atomic_label', 'x', 'y', and 'z' as keys.
    """
    atoms = []

    # Regular expression to match the data rows (excluding the radius)
    atom_pattern = re.compile(
        r"\s*(\d+)\s+(\w+)\s+\w\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)"
    )

    parsing = False
    for line in content:
        if "Final asymmetric unit coordinates" in line:
            parsing = True
            continue

        # TODO: Change the way it work
        if "Final Cartesian" in line:
            break

        if "--------" in line:
            continue

        if parsing:
            match = atom_pattern.match(line)
            if match:
                # Extract atom information from the matched line
                _no, atomic_label, x, y, z = match.groups()
                atom_data = [
                    atomic_label,
                    float(x),
                    float(y),
                    float(z),
                ]
                atoms.append(atom_data)

    return atoms


def read_energy(content):
    """
    Read energy from GULP job file.

    Returns:
        Energy of the structure in eV
    """
    energy_in_eV = 10**5
    for line in content:
        if "Total lattice energy" in line and line.strip().split()[-1] == "eV":
            try:
                energy_in_eV = float(line.strip().split()[-2])
            except ValueError:
                energy_in_eV = 10**5

    return energy_in_eV


def read_bulk_shear(content, pattern="Bulk  Modulus (GPa)"):
    values = [10**5] * 3
    for line in content:
        if pattern in line:
            _ = line.split("=")
            try:
                values = list(map(float, _[-1].split()))
            except ValueError:
                values = [10**5] * 3
    return values


def parse_elastic_constant_matrix(content):
    """
    Extract the Elastic Constant Matrix from the given text content.

    Parameters:
    content (list of str): The lines of the text file or content.

    Returns:
    list of list: A 2D list where each inner list represents a row in the
                  elastic constant matrix.
    """
    matrix = []
    in_matrix_section = False

    # Regular expression to match matrix rows # FIXME fails if 1233.1231-1234.5123
    row_pattern = re.compile(r"^\s*(\d+)\s+([\d\.\-\s]+)")

    for line in content:
        # Detect the start of the Elastic Constant Matrix section
        if "Elastic Constant Matrix" in line:
            in_matrix_section = True
            continue

        # Detect the end of the matrix section or a new section
        if in_matrix_section and "Elastic Compliance Matrix" in line:
            break

        # Skip separators
        if "--------" in line:
            continue

        # Extract matrix rows
        if in_matrix_section:
            match = row_pattern.match(line)
            if match:
                row_values = list(map(float, match.group(2).split()))
                matrix.append(row_values)

    return matrix if matrix else [[10**5] * 6] * 6


def parse_to_pyxtal(content):   
    atoms = read_asymmetric_unit(content)
    cell_params = read_cell_parameters(content)

    a, b, c = cell_params[0:3]
    alpha, beta, gamma = cell_params[3:6]

    lattice = Lattice.from_parameters(a, b, c, alpha, beta, gamma)

    species = []
    for atom in atoms:
        element_symbol = atom[0]
        species.append(Element(element_symbol))

    coords = [[atom[1], atom[2], atom[3]] for atom in atoms]

    structure = Structure(
        lattice=lattice,
        species=species,
        coords=coords,
        coords_are_cartesian=False,
        validate_proximity=True
    )

    crystal = pyxtal()
    crystal.from_seed(structure)

    return crystal
