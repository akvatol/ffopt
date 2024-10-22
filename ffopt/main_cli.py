import pathlib
import tomllib

import click

from ffopt.core.pipeline import OptimizationPipeline
from ffopt.jobs.utils import process_res


@click.command()
@click.argument("input_file")
def main(input_file):
    click.echo("Read input data.")
    with open(input_file, 'r') as f:
        toml = f.readlines()
        toml = ''.join(toml)
    data = tomllib.loads(toml)
    # TODO WHY IS IT HERE?
    input_file = pathlib.Path(input_file)
    app = OptimizationPipeline.from_dict(data)
    # TODO: RES attr object {X:np.array, F:np.array} 
    res = app.optimize()
    process_res(res, input_file)


if __name__ == '__main__':
    main()