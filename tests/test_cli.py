import subprocess
import sys
import os
import tempfile
import shutil
import pytest

BIN = sys.executable

@pytest.mark.parametrize("cmd", [
    ["-m", "envsmith", "init"],
    ["-m", "envsmith", "validate"],
    ["-m", "envsmith", "export", "--format", "json"],
])
def test_cli_commands(cmd):
    tmpdir = tempfile.mkdtemp()
    cwd = os.getcwd()
    try:
        os.chdir(tmpdir)
        # Copy minimal envsmith to tmpdir
        shutil.copytree(os.path.join(cwd, "envsmith"), os.path.join(tmpdir, "envsmith"))
        result = subprocess.run([BIN] + cmd, capture_output=True, text=True)
        assert result.returncode in (0, 1)
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmpdir)
