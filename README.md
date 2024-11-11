# ffopt

**Version**: 0.5.0  
**License**: MIT  
**Author**: Anton Domnin (a.v.daomnin [at] gmail.com)

---

`ffopt` is a simple tool for force-field optimization. It provides functionality for multi-objective optimization via GULP software.

---

## Table of Contents
1. [Installation](#installation)
2. [Usage](#usage)

---

## Installation

**Requirements**:
- Python 3.10 or higher
- [GULP software](https://gulp.curtin.edu.au/)

To install it from source:

```bash
git clone https://github.com/akvatol/ffopt.git
cd ffopt
pip install -r requirements.txt
pip install .
```

## Usage

To use it, you should build a configuration file and bunch support files like 'force-field.template' and 'bounds.txt'. After you make all required files, you can simply run it like:

```
ffopt-cli path/to/config.toml
```


