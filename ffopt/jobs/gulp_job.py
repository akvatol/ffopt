"Job - container for all systems and ruls for generating input files"


class GulpJob():
    def __init__(self, structures, gulp_path, gulp_settings, ff_template):
        pass

    def _generate_input(self, structure, ff_values) -> str:
        "Method for generation input files for GULP."
        pass

    def _calc_task(self, structure, ff_values) -> dict:
        pass

    def get_target_values(self):
        pass

    def run_job(self, ff_values) -> tuple:
        pass