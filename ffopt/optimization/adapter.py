import numpy as np
from joblib import Parallel, delayed
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.algorithms.moo.unsga3 import UNSGA3
from pymoo.core.evaluator import Evaluator
from pymoo.core.problem import Problem
from pymoo.core.termination import NoTermination
from pymoo.problems.static import StaticProblem
from pymoo.util.ref_dirs import get_reference_directions

from ffopt.jobs.utils import _get_mins_maxs, read_bounds_file
from ffopt.optimization.base import OptimizationStrategy


# 1) Определяю алгоритм и параметры 2) Определяю проблему 3) запуск
class PymooMOAdapter(OptimizationStrategy):
    def __init__(
        self,
        algorithm,
        problem,
        n_gen: int,
        n_errors: int,
        n_jobs: int,
        variable_names: list,
    ):
        """
        Arguments
        ---------
        algorithm - pymoo MO algorithm
        problem - pymoo problem
        n_gen - number of generation
        n_errors - number of errors
        n_jobs - number of process that will be used
        """
        self.algorithm = algorithm
        self.problem = problem
        self.n_gen = n_gen
        self.n_errors = n_errors
        self.n_jobs = n_jobs
        self.variable_names = variable_names

    def run(self, error_function, initial_guess=None):
        self.algorithm.setup(self.problem, termination=NoTermination())
        for i in range(self.n_gen):
            print(i + 1)
            pop = self.algorithm.ask()
            X = pop.get("X")
            data = Parallel(n_jobs=self.n_jobs)(
                delayed(error_function)(
                    dict(zip(self.variable_names, x, strict=False))
                )
                for x in X
            )
            F = np.array(data)

            # callback.notify(X=X, F=F)
            static = StaticProblem(self.problem, F=F)
            Evaluator().eval(static, pop)

            # returned the evaluated individuals which have been evaluated
            self.algorithm.tell(infills=pop)

        res = self.algorithm.result()
        return res

    def get_guess(self):
        return self.algorithm.reslut().X

    def _define_problem(
        self,
        *,
        num_errors: int,
        num_variables: int,
        variable_bounds: dict[str, tuple[float, float]],
    ) -> Problem:
        """Define a PyMOO problem instance.

        Returns:
        Problem: An instance of the MyProblem class.
        """

        class MyProblem(Problem):
            def __init__(self, **kwargs):
                xl, xu = _get_mins_maxs(variable_bounds)
                super().__init__(
                    n_var=num_variables,
                    n_obj=num_errors,
                    n_ieq_constr=0,
                    xl=xl,
                    xu=xu,
                    **kwargs,
                )

        return MyProblem()

    @staticmethod
    def _initialize_algorithm(algorithm_name, params):
        """
        Parameters:
        - algorithm_name (str):  Возможные значения: 'CTAEA', 'NSGA3', 'UNSGA3'.
        - params (dict): Словарь с параметрами для инициализации алгоритма.

        Returns:
        - object: Инициализированный экземпляр алгоритма.

        Raises:
        - ValueError: Если передано некорректное имя алгоритма.
        """

        if algorithm_name == "UNSGA3":
            return UNSGA3(**params)
        elif algorithm_name == "NSGA3":
            return NSGA3(**params)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm_name}")

    @classmethod
    def from_dict(cls, data):
        bounds, n_var, variable_names = read_bounds_file(data["bounds"])
        data["ref_dirs"] = get_reference_directions(
            "das-dennis", int(data["n_errors"]), n_partitions=n_var
        )

        algorithm = cls._initialize_algorithm(data["name"], data)
        problem = cls._define_problem(int(data["n_errors"]), n_var, bounds)
        return cls(
            algorithm=algorithm,
            problem=problem,
            n_gen=int(data["n_gen"]),
            n_errors=int(data["n_errors"]),
            n_jobs=int(data["n_jobs"]),
            variable_names=variable_names,
        )
