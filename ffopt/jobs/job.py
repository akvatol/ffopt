from ffopt.jobs.gulp_job import GulpJob
from ffopt.parsers.gulp import GulpSParser


class Job():
    def __init__(*args, **kwargs):
        pass

    # FIXME: затычка
    def get_tools(*args, **kwargs):
        return GulpJob, GulpSParser