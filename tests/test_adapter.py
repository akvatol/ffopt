# test_pymoo_adapter.py

import numpy as np
import pytest
from pymoo.algorithms.soo.nonconvex.de import DE
from pymoo.algorithms.soo.nonconvex.es import ES
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.algorithms.soo.nonconvex.isres import ISRES
from pymoo.core.problem import Problem

from ffopt.jobs.utils import _get_mins_maxs
from ffopt.optimization.adapter import PymooMOAdapter


# Since read_bounds_file is from an external module, we'll mock it
def mock_read_bounds_file(file_path):
    # Mocked data
    bounds = {
        'x1': (0, 10),
        'x2': (0, 5),
        'x3': (-5, 5)
    }
    n_var = 3
    variable_names = ['x1', 'x2', 'x3']
    return bounds, n_var, variable_names


# Mock objective function
def mock_objective_function(x_dict):
    x = list(x_dict.values())
    return sum(xi**2 for xi in x)


def test_get_mins_maxs():
    variable_bounds = {
        'x1': (0, 10),
        'x2': (-5, 5),
        'x3': (2, 8)
    }
    expected_mins = [0, -5, 2]
    expected_maxs = [10, 5, 8]
    var_min, var_max = _get_mins_maxs(variable_bounds)
    assert var_min == expected_mins, "Minimum bounds are incorrect."
    assert var_max == expected_maxs, "Maximum bounds are incorrect."


def test_pymoo_adapter_init():
    algorithm = GA(pop_size=10)
    problem = Problem(n_var=3, n_obj=1, xl=[0, 0, 0], xu=[1, 1, 1])
    n_gen = 5
    n_errors = 1
    n_jobs = 1
    variable_names = ['x1', 'x2', 'x3']
    adapter = PymooMOAdapter(
        algorithm,
        problem,
        n_gen,
        n_errors,
        n_jobs,
        variable_names)
    assert adapter.algorithm is algorithm, "Algorithm not set correctly."
    assert adapter.problem is problem, "Problem not set correctly."
    assert adapter.n_gen == n_gen, "Number of generations not set correctly."
    assert adapter.n_errors == n_errors, "Number of errors not set correctly."
    assert adapter.n_jobs == n_jobs, "Number of jobs not set correctly."
    assert adapter.variable_names == variable_names, "Variable names not set correctly."


def test_initialize_algorithm():
    params = {'pop_size': 20}
    algorithm = PymooMOAdapter._initialize_algorithm('DE', params)
    assert isinstance(algorithm, DE), "Algorithm is not an instance of DE."
    assert algorithm.pop_size == 20, "Algorithm parameters not set correctly."

    algorithm = PymooMOAdapter._initialize_algorithm('ES', params)
    assert isinstance(algorithm, ES), "Algorithm is not an instance of ES."

    algorithm = PymooMOAdapter._initialize_algorithm('GA', params)
    assert isinstance(algorithm, GA), "Algorithm is not an instance of GA."

    algorithm = PymooMOAdapter._initialize_algorithm('ISRES', params)
    assert isinstance(algorithm, ISRES), "Algorithm is not an instance of ISRES."

    with pytest.raises(ValueError):
        PymooMOAdapter._initialize_algorithm('Unknown', params)


def test_define_problem():
    adapter = PymooMOAdapter(
        algorithm=GA(),
        problem=None,  # Will be set by _define_problem
        n_gen=5,
        n_errors=1,
        n_jobs=1,
        variable_names=['x1', 'x2', 'x3']
    )
    variable_bounds = {
        'x1': (0, 1),
        'x2': (-1, 1),
        'x3': (2, 3)
    }
    num_errors = 1
    num_variables = 3
    problem = adapter._define_problem(
        num_errors=num_errors,
        num_variables=num_variables,
        variable_bounds=variable_bounds
    )
    assert isinstance(problem, Problem), "Returned object is not an instance of Problem."
    assert problem.n_var == num_variables, "Number of variables not set correctly in Problem."
    assert problem.n_obj == num_errors, "Number of objectives not set correctly in Problem."
    expected_xl = [0, -1, 2]
    expected_xu = [1, 1, 3]
    assert problem.xl.tolist() == expected_xl, "Lower bounds not set correctly in Problem."
    assert problem.xu.tolist() == expected_xu, "Upper bounds not set correctly in Problem."


def test_pymoo_adapter_run():
    # Mock the problem
    class MyProblem(Problem):
        def __init__(self):
            super().__init__(n_var=3, n_obj=1, xl=[0, 0, 0], xu=[1, 1, 1])

    # Mock algorithm
    algorithm = GA(pop_size=5)
    problem = MyProblem()
    n_gen = 2
    n_errors = 1
    n_jobs = 1
    variable_names = ['x1', 'x2', 'x3']

    adapter = PymooMOAdapter(algorithm, problem, n_gen, n_errors, n_jobs, variable_names)

    # Mock objective function
    def mock_error_function(x_dict):
        x = np.array(list(x_dict.values()))
        return np.sum(x ** 2)

    result = adapter.run(mock_error_function)

    # Verify that result is as expected
    assert hasattr(result, 'X'), "Result does not have attribute 'X'."
    assert hasattr(result, 'F'), "Result does not have attribute 'F'."
    assert len(result.X) == 3, "Resulting X does not have correct dimensions."