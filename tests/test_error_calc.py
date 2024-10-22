from ffopt.jobs.error_calculator import (
    ErrorCalculator,
    get_data_by_index,
    get_data_kpoints,
    grouping_rule,
    process_atoms,
    generate_data_indexes
)


def test_get_data_by_index():
    data = [[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]]
    index = [[2, 1]]
    result = get_data_by_index(data, index)
    assert result == [7, 8, 9]


def test_get_data_kpoints():
    target = [[1, 2, 3], [4, 5]]
    calculated = [[-1000], [4, 5, 6]]
    data1, data2 = get_data_kpoints(target, calculated)
    assert data1 == [1, 2, 3, 4, 5]
    assert data2 == [-1000, -1000, -1000, 4, 5]

    # Additional test cases
    # Case when target and calculated have matching lengths
    target = [[1, 2], [3]]
    calculated = [[1, 2], [3, 4]]
    data1, data2 = get_data_kpoints(target, calculated)
    assert data1 == [1, 2, 3]
    assert data2 == [1, 2, 3]

    # Case when calculated has more elements than target
    target = [[1, 2]]
    calculated = [[1, 2, 3]]
    data1, data2 = get_data_kpoints(target, calculated)
    assert data1 == [1, 2]
    assert data2 == [1, 2]

    # Case when target or calculated is empty
    target = []
    calculated = []
    data1, data2 = get_data_kpoints(target, calculated)
    assert data1 == []
    assert data2 == []


def test_process_atoms():
    target = [['W', 2, 2, 2, 0, 0, 1], ['S', 3, 3, 3, 1, 0, 1]]
    calculated = [['W', 1, 1, 1], ['S', 3, 4, 6]]
    data1, data2 = process_atoms(target, calculated)
    assert data1 == [2, 3, 3]
    assert data2 == [1, 3, 6]

# TODO
def test_error_calculator_group_data():
    target_values = {
        'system1': {
            'energy': 10.0,
            'atoms': [['W', 2, 2, 2, 1, 0, 0], ['S', 3, 3, 3, 0, 1, 0]],
        }
    }
    calculated_values = {
        'energy': 9.5,
        'atoms': [['W', 2.1, 2.0, 2.0], ['S', 3.0, 3.1, 3.0]],
    }
    data_indexes = {}

    calculator = ErrorCalculator(target_values, calculated_values)
    groups = calculator.group_data(grouping_rule, data_indexes)

    assert target_values['system1']['energy'] in groups[1]['target']
    assert len(groups) == 2
    assert len(groups[2]['target']) == 2


def test_error_calculator_calculate_errors():
    target_values = {
        'system1': {
            'energy': 10.0,
            'atoms': [['W', 2, 2, 2, 1, 0, 1], ['S', 3, 3, 3, 0, 1, 0]],
            'bulk_values': 123,
            'bulk_index': [2]
        }
    }
    calculated_values = {
        'system1': {
            'energy': 9.5,
            'atoms': [['W', 2.1, 2.0, 2.0], ['S', 3.0, 3.1, 3.0]],
            'bulk_values': [54, 123, 17]}
    }
    data_indexes = generate_data_indexes(target_values)

    calculator = ErrorCalculator(target_values, calculated_values)
    groups = calculator.group_data(grouping_rule, data_indexes)
    errors = calculator.calculate_errors(groups, metric="mae")

    assert len(errors) == 3
    assert errors[2] == 0
