from pathlib import Path

from ffopt.core.software_runner import Process, execute_process
from ffopt.jobs.error_calculator import (
    ErrorCalculator,
    generate_data_indexes,
    grouping_rule,
)
from ffopt.jobs.job import Job


class FunctionFactory():
    def __init__(self, 
                 calc_objects: dict,
                 software_options: dict,
                 pipeline: dict):
        """
        args - GulpJob ojects
        kwargs - settings
        """
        self.container = calc_objects
        self.software_options = software_options
        self.pipeline = pipeline

    def generate_err_funcs(self):
        data = []
        for alg in self.pipeline:
            data.append(
                self.generate_err_func(
                    objects=self.container,
                    software_options=self.software_options,
                    algorith_info=self.pipeline[alg],
                    extra_options=self.pipeline[alg].get('software')
                    )
                )
        return data

    def generate_err_func(self,
                          objects: dict,
                          software_options,
                          algorith_info,
                          extra_options=None):
        # Если MOO,
        # то для каждого объекта создаеём GulpJob,
        # Если SOO, всего один инпут по шаблону.
        # генерируем инпуты,
        # запускаем раннер,
        # парсим аут,
        # складываем данные в хранилище считаем ошибку
        # Возврящяем список с ошибками по группам или число
        def err_func(values: dict):
            match algorith_info['type'].upper():
                case 'MOO':
                    res = self.calculate_MOO_task(
                        objects=objects,
                        software_options=software_options,
                        extra_options=extra_options,
                        template=algorith_info['ff_template'],
                        values=values)
                # FIXME Does not work
                case 'SOO':
                    res = self.calculate_SOO_task(
                        software_options,
                        template=algorith_info['calc_template']
                    )
            return res
        return err_func

    # Возвращает рещультаты не считая ошибку
    def calculate_MOO_task(self,
                           objects: dict,
                           software_options,
                           extra_options,
                           template,
                           values) -> dict[str:list[float] | float]:
        data = {}
        for obj in objects:
            ff_template = read_file(template)
            # Get objects that can for with software IO
            job_cls, parser_cls = Job.get_tools(software_options['software'])
            software_options.update(extra_options)
            # Нужен темплат
            job_obj = job_cls(objects[obj], software_options, ff_template)
            gin = job_obj.generate_input(values)
            process = Process(
                args=[Path(software_options['path'])],
                input_data=gin,
                )
            result = execute_process(process)
            content = result.stdout
            parser = parser_cls(filepath=None, content=content.split('\n'))
            parser.parse()
            data[obj] = parser.data

        data_indexes = generate_data_indexes(objects)

        calculator = ErrorCalculator(objects, data)
        # print(ErrorCalculator.target)
        groups = calculator.group_data(grouping_rule, data_indexes)
        errors = calculator.calculate_errors(groups, metric="mae")

        return errors

    # Возвр
    # FIXME
    def calculate_SOO_task(self,
                           software_options,
                           template,
                           values) -> dict[str:float]:
        job_cls, parser_cls = Job.get_tools(software_options['software'], type='SOO')
        job_obj = job_cls(template) 
        gin = job_obj.generate_input(values)
        process = Process(
            args=[Path(software_options['path'])],
            input_data=gin,
            )
        result = execute_process(process)
        parser = parser_cls(content=result)
        parser.parse()
        return parser.data['']

    @classmethod
    def from_dict(cls, data):
        objects = data['model']['structures']
        software_options = data['model']['software']
        pipeline = data['model']['pipeline']
        return cls(objects, software_options, pipeline)


def read_file(path):
    with open(path, 'r') as f:
        data = f.read()
    return data