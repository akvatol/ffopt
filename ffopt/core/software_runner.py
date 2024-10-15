from dataclasses import dataclass
from pathlib import Path
from subprocess import CompletedProcess, run

__all__ = ["Process", "execute_process"]

CAPTURING_ENCODING = "utf-8"


@dataclass(frozen=True)
class Process:
    """
    By default `encoding` is "utf-8".
    Uses shell if `executable` is not provided.

    See:
    * https://docs.python.org/3/library/subprocess.html#subprocess.run
    * https://docs.python.org/3/library/subprocess.html#subprocess.Popen
    """
    args: list[Path | str]
    input_data: str | None = None
    executable: Path | None = None
    timeout: float | None = None
    encoding: str | None = CAPTURING_ENCODING


def execute_process(process: Process) -> CompletedProcess:
    """Simple function for running software.
    >>> execute_process(args=['ls', '-l'])
    >>> execute_process(args=['/path/to/software'], stdin=input_file_data)
    """
    return run(
        executable=process.executable,
        input=process.input_data,
        args=process.args,
        timeout=process.timeout,
        encoding=process.encoding,
        capture_output=True,
        text=True
    )
