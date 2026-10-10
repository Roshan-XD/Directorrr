import json
from unittest.mock import patch

import pytest

from director.resolve.conversion import WindowsVideoConverter


def candidate(tmp_path):
    python = tmp_path / "runtime/windows-dev-001/venv/Scripts/python.exe"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"fixture")
    folder = tmp_path / "generated_videos/development" / ("a" * 32)
    folder.mkdir(parents=True)
    source = folder / "clip.webm"
    source.write_bytes(b"fixture")
    return source, folder / "clip.mp4"


def test_windows_conversion_fixed_process(tmp_path):
    source, output = candidate(tmp_path)
    with patch("director.resolve.conversion.subprocess.run") as run:
        run.return_value.returncode = 0
        run.return_value.stdout = json.dumps({"codec": "h264"})
        assert WindowsVideoConverter(tmp_path)(source, output) == {"codec": "h264"}
        args, kwargs = run.call_args
        assert "wsl.exe" not in args[0]
        assert args[0][-2:] == [str(source), str(output)]
        assert kwargs["shell"] is False and kwargs["timeout"] == 120


def test_windows_conversion_rejects_external_output(tmp_path):
    source, _ = candidate(tmp_path)
    with pytest.raises(ValueError):
        WindowsVideoConverter(tmp_path)(source, tmp_path / "external.mp4")


def test_windows_conversion_failure(tmp_path):
    source, output = candidate(tmp_path)
    with patch("director.resolve.conversion.subprocess.run") as run:
        run.return_value.returncode = 1
        with pytest.raises(ValueError, match="Windows PyAV"):
            WindowsVideoConverter(tmp_path)(source, output)
