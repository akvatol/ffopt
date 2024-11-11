import warnings
from pathlib import Path

import click

from ffopt.core.pipeline import OptimizationPipeline
from ffopt.core.prepare import DataPreparer
from ffopt.jobs.utils import process_res

warnings.filterwarnings("ignore")


@click.command()
@click.argument("input_file")
def main(input_file):
    click.echo("Read input data")
    input_file = Path(input_file)

    data_preparer = DataPreparer(str(input_file))
    data = data_preparer.prepare_data()

    app = OptimizationPipeline.from_dict(data)
    res = app.optimize()
    process_res(res, input_file)


if __name__ == '__main__':
    main()
