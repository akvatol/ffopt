"""Generic optimization pipeline for subsequentall optimization."""
from pathlib import Path

from ffopt.jobs.objective_function import FunctionFactory
from ffopt.jobs.utils import get_callback

# from ffopt.optimization.adapter import AlgorithmAdapter
from ffopt.optimization.adapter import PymooMOAdapter


class OptimizationPipeline:
    """
    A generic optimization pipeline that runs multiple optimization algorithms.

    Each stage corresponds to one optimization algorithm, where the result
    of one stage is used as the initial input for the next.

    Parameters
    ----------
    objective_function : callable
        The function to optimize. Should accept input variables and
        return the value to be minimized.

    algorithms : list
        A list of optimization algorithm instances to be run sequentially.

    constraints : list, optional
        A list of constraint functions or objects defining
        the optimization problem's constraints.

    callback : callable, optional
        A function that is called after each stage of optimization.
    """

    def __init__(self,
                 objective_functions,
                 algorithms,
                 constraints=None,
                 callbacks=None
                 ):
        self.objective_functions = objective_functions
        self.algorithms = algorithms
        # TODO: Ensure it is a best way to send constrains
        self.callbacks = callbacks
        self.constrains = constraints

    # TODO: Write final results in file
    def optimize(self, initial_guess=None,):
        """Run the optimization pipeline sequentially over multiple algorithms.

        Parameters
        ----------
        initial_guess : array-like
            Initial guess for the optimization variables.

        Returns
        -------
        dict : A dict with the optimization results after the final stage.
        """
        current_guess = initial_guess
        result = None
        iterator = zip(
            self.algorithms,
            # FIXME 
            # self.callbacks,
            self.objective_functions,
            strict=True
            )

        # FIXME
        # for i, algorithm, callback, objective_function in enumerate(iterator):
        for i, (algorithm, objective_function) in enumerate(iterator):
            print(f"Running stage {i + 1} with {algorithm.__class__.__name__}")

            result = algorithm.run(
                objective_function,
                initial_guess=current_guess,
                # FIXME
                callback=None
            )

            # Update the guess for the next stage
            current_guess = algorithm.get_guess()

        return result

    @classmethod
    def from_dict(cls, data: dict):

        objective_functions = FunctionFactory.from_dict(
            data
        ).generate_err_funcs()

        algorithms = [
            # TODO Заменить на AlgorithmAdapter
            PymooMOAdapter.from_dict(data["model"]["pipeline"][i])
            for i in sorted(data["model"]["pipeline"].keys())
        ]
        # TODO: Должно выглядеть иначе, это затычка
        callbacks = get_callback(data["model"])
        obj = cls(
            objective_functions=objective_functions,
            algorithms=algorithms,
            callbacks=callbacks,
        )
        return obj