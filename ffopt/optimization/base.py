from abc import ABC, abstractmethod


class OptimizationStrategy(ABC):

    @abstractmethod
    def get_guess(self):
        pass

    @abstractmethod
    def run(self, objective_function, initial_guess):
        pass