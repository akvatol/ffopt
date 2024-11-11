from pathlib import Path
from subprocess import TimeoutExpired

import pytest

from ffopt.core.software_runner import Process, execute_process


def test_execute_simple_command():
    process = Process(args=['echo', 'Hello, World!'])
    result = execute_process(process)
    assert result.stdout.strip() == 'Hello, World!'
    assert result.returncode == 0


def test_execute_with_input_data():
    process = Process(
        args=['grep', 'World'],
        input_data='Hello, World!\nHello, Python!'
    )
    result = execute_process(process)
    assert result.stdout.strip() == 'Hello, World!'
    assert result.returncode == 0


def test_execute_nonexistent_command():
    process = Process(args=['nonexistentcommand'])
    with pytest.raises(FileNotFoundError):
        execute_process(process)


def test_execute_command_with_timeout():
    process = Process(
        args=['sleep', '2'],
        timeout=1
    )
    with pytest.raises(TimeoutExpired):
        execute_process(process)


def test_execute_command_with_path_args():
    script_path = Path('/bin/echo')
    process = Process(args=[script_path, 'Test'])
    result = execute_process(process)
    assert result.stdout.strip() == 'Test'
    assert result.returncode == 0


def test_encoding_handling():
    # Assuming the system supports UTF-8 characters
    process = Process(args=['echo', 'Привет, мир!'])
    result = execute_process(process)
    assert result.stdout.strip() == 'Привет, мир!'
    assert result.returncode == 0


def test_invalid_encoding():
    process = Process(args=['echo', 'Hello'], encoding='invalid-encoding')
    with pytest.raises(LookupError):
        execute_process(process)
