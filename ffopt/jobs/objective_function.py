from pathlib import Path

from ffopt.core.software_runner import Process, execute_process
from ffopt.jobs.error_calculator import (
    ErrorCalculator,
    generate_data_indexes,
    grouping_rule,
)
from ffopt.jobs.job import Job


class FunctionFactory:
    def __init__(
        self, calc_objects: dict, software_options: dict, pipeline: dict
    ):
        """
        Initializes the FunctionFactory.

        Args:
            calc_objects (dict): Calculation objects for MOO or SOO tasks.
            software_options (dict): Software configuration options.
            pipeline (dict): Pipeline settings defining algorithms and templates.
        """
        self.container = calc_objects
        self.software_options = software_options
        self.pipeline = pipeline

    def generate_err_funcs(self):
        """
        Generates error functions for each algorithm in the pipeline.

        Returns:
            list[callable]: A list of error functions.
        """
        return [
            self.generate_err_func(
                objects=self.container,
                software_options=self.software_options,
                algorith_info=alg_info,
                extra_options=alg_info.get("software"),
            )
            for alg_info in self.pipeline.values()
        ]

    def generate_err_func(
        self,
        objects: dict,
        software_options,
        algorith_info,
        extra_options=None,
    ):
        """
        Generates an error function based on algorithm information.

        Args:
            objects (dict): Calculation objects.
            software_options (dict): Software options for configuration.
            algorith_info (dict): Information about the algorithm.
            extra_options (dict, optional): Extra software options.

        Returns:
            callable: An error function that calculates errors based on algorithm type.
        """
        task_type = algorith_info.get("type", "").upper()

        def err_func(values: dict):
            if task_type == "MOO":
                return self.calculate_MOO_task(
                    objects,
                    software_options,
                    extra_options,
                    algorith_info["ff_template"],
                    values,
                )
            elif task_type == "SOO":
                return self.calculate_SOO_task(
                    software_options, algorith_info["calc_template"], values
                )
            else:
                raise ValueError(f"Unsupported task type: {task_type}")

        return err_func

    def calculate_MOO_task(
        self, objects: dict, software_options, extra_options, template, values
    ) -> dict[str, list[float] | float]:
        """
        Calculates the Multi-Objective Optimization (MOO) task.

        Args:
            objects (dict): Calculation objects.
            software_options (dict): Software options.
            extra_options (dict): Additional software options.
            template (str): Path to the force field template.
            values (dict): Input parameter values.

        Returns:
            dict: Calculated errors grouped by objective.
        """
        data = {}
        software_options.update(extra_options or {})
        job_cls, parser_cls = Job.get_tools(software_options["software"])

        for obj_name, obj_data in objects.items():
            ff_template = read_file(template)
            job_obj = job_cls(obj_data, software_options, ff_template)
            gin = job_obj.generate_input(values)

            process = Process(
                args=[Path(software_options["path"])], input_data=gin
            )
            result = execute_process(process)
            parser = parser_cls(
                filepath=None, content=result.stdout.split("\n")
            )
            parser.parse()
            data[obj_name] = parser.data

        calculator = ErrorCalculator(objects, data)
        groups = calculator.group_data(grouping_rule)
        return calculator.calculate_errors(groups, metric="mae")

    def calculate_SOO_task(
        self, software_options, template, values
    ) -> dict[str, float]:
        """
        Calculates the Single Objective Optimization (SOO) task.

        Args:
            software_options (dict): Software options.
            template (str): Template for calculation.
            values (dict): Input parameter values.

        Returns:
            dict: Calculated single objective value.
        """
        job_cls, parser_cls = Job.get_tools(
            software_options["software"], type="SOO"
        )
        job_obj = job_cls(template)
        gin = job_obj.generate_input(values)

        process = Process(
            args=[Path(software_options["path"])], input_data=gin
        )
        result = execute_process(process)
        parser = parser_cls(content=result.stdout)
        parser.parse()
        return parser.data.get("")

    @classmethod
    def from_dict(cls, data):
        """
        Constructs FunctionFactory from a dictionary configuration.

        Args:
            data (dict): Configuration dictionary.

        Returns:
            FunctionFactory: An instance of FunctionFactory.
        """
        objects = data["model"]["structures"]
        software_options = data["model"]["software"]
        pipeline = data["model"]["pipeline"]
        return cls(objects, software_options, pipeline)


def read_file(path):
    """
    Reads the content of a file.

    Args:
        path (str): The file path.

    Returns:
        str: The file content.
    """
    with open(path, "r") as f:
        return f.read()
