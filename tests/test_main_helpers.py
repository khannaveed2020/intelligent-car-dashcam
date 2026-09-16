from pathlib import Path

import pytest

from app import main
from app.video_processor import VideoValidationError


class FakeUpload:
    def __init__(self, name: str, content: bytes):
        self.name = name
        self.content = content
        self.size = len(content)

    def getbuffer(self) -> bytes:
        return self.content


def test_save_upload_uses_generated_internal_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data_dir = (tmp_path / "data").resolve()
    monkeypatch.setattr(main, "DATA_DIR", data_dir)

    video_path, session_dir = main.save_upload(FakeUpload("../../private.mp4", b"video"))

    assert video_path == session_dir / "upload.mp4"
    assert video_path.read_bytes() == b"video"
    assert session_dir.parent == data_dir


def test_remove_session_files_removes_only_child_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data_dir = (tmp_path / "data").resolve()
    session_dir = data_dir / "session"
    session_dir.mkdir(parents=True)
    (session_dir / "upload.mp4").write_bytes(b"video")
    monkeypatch.setattr(main, "DATA_DIR", data_dir)

    main.remove_session_files(session_dir)

    assert not session_dir.exists()


def test_remove_session_files_rejects_outside_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data_dir = (tmp_path / "data").resolve()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    monkeypatch.setattr(main, "DATA_DIR", data_dir)

    with pytest.raises(VideoValidationError, match="outside"):
        main.remove_session_files(outside_dir)

    assert outside_dir.exists()
