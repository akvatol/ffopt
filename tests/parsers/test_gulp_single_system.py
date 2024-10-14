import pytest

from ffopt.parsers.gulp import GulpSParser

TEST_GAMMA_PATH = 'test_files/WS2_gamma.out'
TEST_KPOINTS_PATH = 'test_files/WS2_kpoints.out'


@pytest.fixture
def kpoints():
    parser = GulpSParser(TEST_KPOINTS_PATH)
    parser.pop_extractor('phonon_gamma')
    parser.parse()
    return parser


@pytest.fixture
def gamma():
    parser = GulpSParser(TEST_GAMMA_PATH)
    parser.pop_extractor('phonon_kpoints')
    parser.parse()
    return parser


def test_energy(gamma: GulpSParser):
    assert gamma.data['energy'] == -26.43930959


def test_atoms(gamma: GulpSParser):
    assert gamma.data['atoms'] == [
        {'no': 1, 'atomic_label': 'W', 'x': 0.333333, 'y': 0.666667, 'z': 0.25},
        {'atomic_label': 'S', 'no': 2, 'x': 0.333333, 'y': 0.666667, 'z': 0.617384}
        ]


def test_cell(gamma: GulpSParser):
    assert gamma.data['cell'] == {
        'a': {'value': 3.131275, 'unit': 'Angstrom'},
        'b': {'value': 3.131275, 'unit': 'Angstrom'},
        'c': {'value': 11.962444, 'unit': 'Angstrom'},
        'alpha': {'value': 90.0, 'unit': 'Degrees'},
        'beta': {'value': 90.0, 'unit': 'Degrees'},
        'gamma': {'value': 120.0, 'unit': 'Degrees'}
        }

def test_bulk_modulus(gamma: GulpSParser):
    """Test the bulk modulus data."""
    assert gamma.data['bulk_modulus'] == [46.90058, 65.47213, 56.18635]


def test_shear_modulus(gamma: GulpSParser):
    """Test the shear modulus data."""
    assert gamma.data['shear_modulus'] == [26.71928, 39.42434, 33.07181]


def test_young_modulus(gamma: GulpSParser):
    """Test the young modulus data."""
    assert gamma.data['young_modulus'] == [153.46736, 153.46736, 57.80293]


def test_elastic_modulus(gamma: GulpSParser):
    """Test the elastic modulus matrix data."""
    assert gamma.data['elastic_modulus'][1][1] == 174.2320


def test_phonon_gamma(gamma: GulpSParser):
    """Test the phonon gamma data."""
    assert gamma.data['phonon_gamma'][0] == 0.0
    assert gamma.data['phonon_gamma'][-1] == 600.04


def test_phonon_kpoints(kpoints: GulpSParser):
    assert kpoints.data['phonon_kpoints'][0][0] == 0.0
    assert kpoints.data['phonon_kpoints'][0][-1] == 600.04
    assert kpoints.data['phonon_kpoints'][1][0] == 17.78
    assert kpoints.data['phonon_kpoints'][1][-1] == 595.19
    assert kpoints.data['phonon_kpoints'][2][0] == 100.60
    assert kpoints.data['phonon_kpoints'][2][-1] == 524.42