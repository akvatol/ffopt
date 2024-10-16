import re

import numpy as np


def read_bounds_file(file_path: str) -> tuple[
    dict[str, tuple[float, float]],
    int,
    list[str]]:
    """
    Читает файл с границами переменных и возвращает кортеж:
    - Словарь с именами переменных и их границами (tuple[float, float]).
    - Количество переменных.
    - Список имен переменных.
    
    Parameters:
    - file_path (str): Путь к файлу с границами переменных.
    
    Returns:
    - tuple[dict[str, tuple[float, float]], int, list[str]]:
      - Словарь с границами переменных.
      - Количество переменных.
      - Список имен переменных.
    """
    
    variable_bounds = {}
    variable_names = []

    with open(file_path, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) != 3:
                continue

            var_name = parts[0]
            lower_bound = float(parts[1])
            upper_bound = float(parts[2])

            variable_bounds[var_name] = (lower_bound, upper_bound)
            variable_names.append(var_name)

    num_variables = len(variable_names)

    return variable_bounds, num_variables, variable_names


def replace_placeholders(template_str, values_dict):
    """
    Replace placeholders in the format <<key>> with
    corresponding values from values_dict.

    Parameters:
    - template_str (str): The template string containing placeholders.
    - values_dict (dict): Dictionary mapping keys to their replacement values.

    Returns:
    - str: The template string with placeholders
    replaced by their corresponding values.
    """
    pattern = re.compile(r"<<(\w+)>>")

    def replacer(match):
        key = match.group(1)
        if key in values_dict:
            return str(values_dict[key])
        else:
            raise KeyError(f"Key '{key}' not found in values_dict")

    result = pattern.sub(replacer, template_str)
    return result


def _get_mins_maxs(variable_bounds: dict) -> tuple[list[float], list[float]]:
    var_min = [min(i) for i in variable_bounds.values()]
    var_max = [max(i) for i in variable_bounds.values()]
    return var_min, var_max


# TODO
def get_callback(data: dict):
    pass


# FIXME
def process_res(res, path, constrains=None):
    fields_path = path.parent.joinpath('fields.csv')
    errors_path = path.parent.joinpath('errors.csv')
    np.savetxt(fields_path, res.X, delimiter=' ', fmt='%.5f')
    np.savetxt(errors_path, res.F, delimiter=' ', fmt='%.5f')