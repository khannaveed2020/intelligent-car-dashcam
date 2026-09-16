import sys

from app import cli


def test_cli_builds_portable_streamlit_command(monkeypatch) -> None:
    captured_arguments: list[str] = []

    def fake_main() -> None:
        captured_arguments.extend(sys.argv)

    monkeypatch.setattr(cli.streamlit_cli, "main", fake_main)
    monkeypatch.setattr(sys, "argv", ["roadlens", "--server.port=9000"])

    cli.main()

    assert captured_arguments[:2] == ["streamlit", "run"]
    assert captured_arguments[2].endswith("app\\main.py") or captured_arguments[2].endswith(
        "app/main.py"
    )
    assert "--server.maxUploadSize=100" in captured_arguments
    assert "--browser.gatherUsageStats=false" in captured_arguments
    assert captured_arguments[-1] == "--server.port=9000"
