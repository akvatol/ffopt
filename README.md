# ffopt

**Version**: 0.5.0  
**License**: MIT  
**Author**: Anton Domnin ([a.v.daomnin@gmail.com](mailto:a.v.daomnin@gmail.com))

---

`ffopt` is a simple tool for force-field optimization. It provides functionality for multi-objective optimization via GULP software.

---

## Table of Contents
1. [Installation](#installation)
2. [Usage](#usage)
3. [Features](#features)
4. [Dependencies](#dependencies)
5. [Development and Testing](#development-and-testing)
6. [License](#license)
7. [Contact](#contact)

---

## Installation

**Requirements**:
- Python 3.10 or higher
- [GULP software](https://gulp.curtin.edu.au/)

To install it from source:

```bash
git clone https://github.com/yourusername/ffopt.git
cd ffopt
pip install -r requirements.txt
pip install .
```

## Usage

To use it, you should build a configuration file and bunch support files like 'force-field.template' and 'bounds.txt' (see below). After you make all required files, you can simply run it like:

```
ffopt-cli path/to/config.toml
```

###

**Software settings**
All optimization configs are stored in a single file, here is an example:

```toml
[model]
[model.software]
software = 'gulp'
path = '/home/mpds_code/gulp-6.1.0/Src/gulp'
xtol = 12
time = 50
[model.structures]
[model.structures.1T_WS2]
# g1
energy = -13.4567
# g2
structure = 'test_files/WS2_2H.cif'
# g3
kpoints_index = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.5], [0.5, 0.0, 0.0]]
kpoints_values = [[0, 0, 0, 27.4, 27.4, 45], [19.0, 19.0, 19.0, 19.0], [158.6, 158.6, 160.6, 160.6]]
# g4
elastic_index = [[1, 1], [3, 3], [4, 4]]
elastic_values = [262.0, 53.0, 13.0]
bulk_index = [2]
bulk_modulus = 63.0
youngs_index = [1, 2, 3]
youngs_modulus = [248.0, 248.0, 52.0]
[model.structures.3R_WS2]
structure = '''cell
3.1580    3.1580   18.4900   90.0000   90.0000  120.0000   1 1 1 0 0 0#  J. Solid State Chem. (1987), 70, 207, 209. Schutte W.J., De Boer J.L., Jellinek F.
frac
W       0.000000000000    0.000000000000    0.000000000  0.000  0 0 0
S       0.000000000000    0.000000000000    0.581000000  0.000  1 1 1
S       0.000000000000    0.000000000000    0.750300000  0.000  1 1 1
W       0.666666666667    0.333333333333    0.333330000  0.000  1 1 1
S       0.666666666667    0.333333333333    0.914330000  0.000  1 1 1
S       0.666666666667    0.333333333333    0.083630000  0.000  1 1 1
W       0.333333333333    0.666666666667    0.666670000  0.000  1 1 1
S       0.333333333333    0.666666666667    0.247670000  0.000  1 1 1
S       0.333333333333    0.666666666667    0.416970000  0.000  1 1 1
space
156'''
sshift = 1.5
energy = -20.179
[model.pipeline]
[model.pipeline.1]
bounds = '/home/mpds_code/code/ffopt/test_files/bounds.txt'
ff_template = '/home/mpds_code/code/ffopt/test_files/simple_template.txt'
type="MOO"
name = "NSGA3"
pop_size = 300
n_gen = 10
n_errors = 4
n_jobs = 1
[model.pipeline.1.software]
time = 30
```


