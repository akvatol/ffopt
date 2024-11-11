from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error


def dict_to_sorted_list(data: dict[int, float]) -> list[float]:
    """
    Converts a dictionary to a sorted list of its values.

    Args:
        data (dict[int, float]): A dictionary with integer keys and float values.

    Returns:
        list[float]: A list of values sorted by the dictionary's keys in ascending order.
    """
    return [value for key, value in sorted(data.items())]


def generate_data_indexes(data_dict: dict):
    """
    Generates a mapping for data indexes based on predefined key patterns.

    Args:
        data_dict (dict): A dictionary with structure data, containing potential keys like
                          'kpoints_index', 'elastic_index', etc.

    Returns:
        dict: A dictionary mapping specific index names to their corresponding values.
    """
    index_map = {
        "kpoints_index": "kpoints_values",
        "elastic_index": "elastic_values",
        "bulk_index": "bulk_modulus",
        "youngs_index": "youngs_modulus",
        "shear_index": "shear_modulus",
    }

    return {
        index_map[key]: value
        for key, value in data_dict.items()
        if key in index_map
    }


def get_data_by_index(data, indices):
    """
    Retrieve elements from nested data structures based on provided indices.

    Args:
        data (list): A nested list structure from which to retrieve elements.
        indices (list): A list of indices, which may contain integers or lists of integers
                        for nested indexing.

    Returns:
        list: A list of elements retrieved based on the indices.
    """
    result = []
    for index in indices:
        sub_result = data
        for idx in index if isinstance(index, list) else [index]:
            sub_result = sub_result[idx - 1]
        if isinstance(sub_result, list):
            result.extend(sub_result)
        else:
            result.append(sub_result)
    return result


def get_data_kpoints(target, calculated):
    """
    Adjusts the lengths of target and calculated k-point data to match.

    Args:
        target (list): The target k-point data list.
        calculated (list): The calculated k-point data list.

    Returns:
        tuple: Two lists (data1, data2) with adjusted lengths.
    """
    data1, data2 = [], []
    for i, j in zip(target, calculated, strict=True):
        j = j * (len(i) // len(j) + 1) if len(i) > len(j) else j
        data1.extend(i)
        data2.extend(j[: len(i)])
    return data1, data2[: len(data1)]


def process_atoms(target, calculated):
    """
    Processes atomic data by applying masks from the target data.

    Args:
        target (list): A list of target atomic data, with masks starting from the fifth element.
        calculated (list): A list of calculated atomic data.

    Returns:
        tuple: Two lists containing selected values based on the masks.
    """
    return (
        [
            i[n + 1]
            for i, j in zip(target, calculated, strict=False)
            for n, mask in enumerate(i[4:])
            if mask
        ],
        [
            j[n + 1]
            for i, j in zip(target, calculated, strict=False)
            for n, mask in enumerate(i[4:])
            if mask
        ],
    )


def process_cell(target, calculated):
    return (
        [
            i
            for i, j in zip(target, calculated, strict=False)
            for n, mask in enumerate(target[6:])
            if mask
        ],
        [
            j
            for i, j in zip(target, calculated, strict=False)
            for n, mask in enumerate(target[6:])
            if mask
        ],
    )


class ErrorCalculator:
    """
    A class for calculating errors between target and calculated values using various metrics.

    Attributes:
        error_functions (dict): A dictionary mapping metric names to sklearn error functions.
    """

    error_functions = {
        "mae": mean_absolute_error,
        "mape": mean_absolute_percentage_error,
    }

    def __init__(self, target_values, calculated_values):
        """
        Initialize the ErrorCalculator with target and calculated values.

        Args:
            target_values (dict): Dictionary of target values for different systems.
            calculated_values (dict): Dictionary of calculated values for the same systems.
        """
        self.target_values = target_values
        self.calculated_values = calculated_values

    def group_data(self, grouping_rule):
        """
        Groups data according to a specified grouping rule.

        Args:
            grouping_rule (callable): A function that takes a key and returns the group name.

        Returns:
            dict: A dictionary where keys are group names, and values are dictionaries
                  containing lists of 'target' and 'calculated' values.
        """
        groups = {}
        for system in self.target_values:
            target_system = self.target_values[system]
            calculated_system = self.calculated_values.get(system, {})
            data_indexes = generate_data_indexes(target_system)
            for key, target in target_system.items():
                group_name = grouping_rule(key)
                calculated = calculated_system.get(key)
                if hasattr(calculated, "__len__"):
                    if key == "kpoints_values":
                        target, calculated = get_data_kpoints(
                            target, calculated
                        )
                    elif index := data_indexes.get(key):
                        calculated = get_data_by_index(calculated, index)
                    elif key == "atoms":
                        target, calculated = process_atoms(target, calculated)
                    elif key == "cell":
                        target, calculated = process_cell(target, calculated)
                if calculated is not None and group_name:
                    if group_name not in groups:
                        groups[group_name] = {"target": [], "calculated": []}
                    groups[group_name]["target"].extend(
                        target if isinstance(target, list) else [target]
                    )
                    groups[group_name]["calculated"].extend(
                        calculated
                        if isinstance(calculated, list)
                        else [calculated]
                    )
        return groups

    def _get_error_func(self, metric):
        """
        Returns the error function for a specified metric.

        Args:
            metric (str): The name of the metric ('mae' or 'mape').

        Returns:
            callable: The sklearn error function corresponding to the metric.

        Raises:
            ValueError: If the metric is not supported.
        """
        try:
            return self.error_functions[metric.lower()]
        except KeyError:
            raise ValueError(f"Unsupported metric: {metric}")  # noqa: B904

    def calculate_errors(self, groups, metric="mae"):
        """
        Calculates error metrics for each group.

        Args:
            groups (dict): The groups dictionary returned by group_data().
            metric (str): The error metric to use ('mae' or 'mape').

        Returns:
            list[float]: A sorted list of calculated error values by group.
        """
        err_func = self._get_error_func(metric)
        errors = {
            group_name: err_func(data["target"], data["calculated"])
            if len(data["target"]) == len(data["calculated"])
            else 10**3
            for group_name, data in groups.items()
        }
        return dict_to_sorted_list(errors)


def grouping_rule(name):
    """
    Groups data keys based on predefined naming conventions.

    Args:
        name (str): The name of the key to group.

    Returns:
        int or None: The group identifier (integer) based on the key name, or None if unmatched.
    """
    match name.lower():
        case "energy":
            return 1
        case "cell" | "atoms":
            return 2
        case "bulk_modulus" | "elastic_values" | "youngs_modulus" | "shear_modulus":
            return 3
        case "kpoints_values":
            return 4
        case _:
            return None
