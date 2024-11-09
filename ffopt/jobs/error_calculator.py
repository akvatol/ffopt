from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from pymatgen.analysis.structure_matcher import StructureMatcher


def dict_to_sorted_list(data: dict[int, float]) -> list[float]:
    """
    Принимает словарь вида dict[int:float] и возвращает список значений,
    отсортированных по ключам в словаре, от меньшего к большему.
    """
    return [value for key, value in sorted(data.items())]


def generate_data_indexes(data_dict):
    data_indexes = {}
    for _key, value in data_dict.items():
        if isinstance(value, dict):
            if "kpoints_index" in value:
                data_indexes["kpoints_values"] = value["kpoints_index"]
            if "elastic_index" in value:
                data_indexes["elastic_values"] = value["elastic_index"]
            if "bulk_index" in value:
                data_indexes["bulk_modulus"] = value["bulk_index"]
            if "youngs_index" in value:
                data_indexes["youngs_modulus"] = value["youngs_index"]
            if "shear_index" in value:
                data_indexes["shear_modulus"] = value["shear_index"]
    return data_indexes


def get_data_by_index(data, indices):
    """
    Получает на вход список индексов вида list[int] или list[list[int, int]] и
    достает данные по индексам из соответствующих массивов.
    """
    result = []
    for index in indices:
        if isinstance(index, list):
            sub_result = data
            for idx in index:
                sub_result = sub_result[idx - 1]
            if isinstance(sub_result, list):
                result.extend(sub_result)
            else:
                result.append(sub_result)
        elif isinstance(index, int):
            sub_result = data[index - 1]
            if isinstance(sub_result, list):
                result.extend(sub_result)
            else:
                result.append(sub_result)
        else:
            raise ValueError(
                "Неверный формат индекса. Ожидается int или list[int, int]"
            )
    return result


def get_data_kpoints(target, calculated):
    data1 = []
    data2 = []
    for i, j in zip(target, calculated, strict=True):
        # Это нужно, чтобы алгоритм правильно срабатывал, если парсер ничего не нашел.
        # т.к. вы этом случае он вернёт [-1000]
        if len(i) > len(j):
            j.extend(j * (len(i) // len(j) + 1))
        data1.extend(i)
        data2.extend(j[: len(i)])

    # Ensure data2 matches the length of data1
    if len(data2) < len(data1):
        data2.extend(data2[: len(data1) - len(data2)])
    elif len(data2) > len(data1):
        data2 = data2[: len(data1)]

    return data1, data2


def process_atoms(target, calculated):
    data1 = [
        i[n + 1]
        for i, j in zip(target, calculated, strict=False)
        for n, mask in enumerate(i[4:])
        if mask
    ]
    data2 = [
        j[n + 1]
        for i, j in zip(target, calculated, strict=False)
        for n, mask in enumerate(i[4:])
        if mask
    ]
    return data1, data2


class ErrorCalculator:
    def __init__(self, target_values, calculated_values):
        """
        Initialize the ErrorCalculator with target and calculated values.

        Parameters:
        - target_values: Dictionary with target values for different systems.
        - calculated_values: Dictionary with new values for the same systems.
        """
        self.target_values = target_values
        self.calculated_values = calculated_values

    def group_data(self, grouping_rule, data_indexes: dict):
        """
        Group data based on the provided grouping rule.

        Parameters:
        - grouping_rule (callable): A function that takes
        a key and returns the group name.

        Returns:
        - groups (dict): A dictionary where keys are group names
        and values are lists of (target, calculated) tuples.
        """
        groups = {}
        # TODO: refactore
        for system in self.target_values:
            target_system = self.target_values[system]
            calculated_system = self.calculated_values[system]
            for key in target_system:
                group_name = grouping_rule(key)
                target = target_system[key]
                calculated = calculated_system.get(key)

                if hasattr(calculated, "__len__"):
                    if key == "kpoints_values":
                        target, calculated = get_data_kpoints(
                            target=target, calculated=calculated
                        )

                    elif index := data_indexes.get(key):
                        calculated = get_data_by_index(calculated, index)

                    elif key == "atoms":
                        target, calculated = process_atoms(
                            target=target, calculated=calculated
                        )

                if calculated is None:
                    continue  # Skip if no calculated value is available

                if group_name:
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

    def _create_structure(self, lattice_params, atoms_data):        
        a, b, c = lattice_params[0:3]
        alpha, beta, gamma = lattice_params[3:6]
        lattice = Lattice.from_parameters(a, b, c, alpha, beta, gamma)
    
        species = []
        coords = []
        for atom in atoms_data:
            species.append(atom[0])
            coords.append(atom[1:4])
        
        return Structure(
            lattice=lattice,
            species=species,
            coords=coords,
            coords_are_cartesian=False
        )

    def _calculate_structure_rmsd(self, target_data, calculated_data):
        target_struct = self._create_structure(
            target_data['lattice_par_dof'], # сделано допущение что в начальных данных при помощи CifParcer есть такой ключ
            target_data['atoms_dof']
        )
        
        calc_struct = self._create_structure(
            calculated_data['cell_parameters'], # допущение что это есть от GulpSparser
            calculated_data['atoms']
        )

        matcher = StructureMatcher(
            ltol=0.2,     
            stol=0.3,     
            angle_tol=5,  
            primitive_cell=True,
            scale=True    
        )
        
        # эта штука по умолчанию вернет None если структуры не эквивалентны
        if matcher.fit(target_struct, calc_struct):
            rms = matcher.get_rms_dist(target_struct, calc_struct)
            return rms 
        else:
            return float('inf')  # вернет большое число если не эквивалентны вместо None

    # TODO: Расширить
    def _get_error_func(self, metric):
        metric = metric.lower()
        if metric == "mae":
            return mean_absolute_error
        elif metric == "mape":
            return mean_absolute_percentage_error
        elif metric == "rmsd": #NEW
            return self._calculate_structure_rmsd
        else:
            raise ValueError(f"Unsupported metric: {metric}")

    def calculate_errors(self, groups, metric="mae"):
        """
        Calculate error metrics for each group.

        Parameters:
        - groups (dict): The groups dictionary returned by group_data().
        - metric (str): The error metric to use ('mae' or 'mape').

        Returns:
        - errors (dict): A dictionary where keys are
        group names and values are the calculated error.
        """
        errors = {}
        err_func = self._get_error_func(metric)
        for group_name, data in groups.items():
            target = data["target"]
            calculated = data["calculated"]
            # TODO нельзя это так оставлять
            if len(target) != len(calculated):
                error = 10**3
            else:
                error = err_func(target, calculated)
            errors[group_name] = error
        return dict_to_sorted_list(errors)


def grouping_rule(name):
    match name.lower():
        case "energy":
            group = 1
        # FIXME
        #         case "cell" | "atoms":
        #             group = 2
        case (
            "bulk_modulus"
            | "elastic_values"
            | "youngs_modulus"
            | "shear_modulus"
        ):
            group = 3
        case "kpoints_values":
            group = 4
        case _:
            group = None
    return group
