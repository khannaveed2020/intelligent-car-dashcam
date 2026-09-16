"""Console launcher for the packaged Streamlit application."""

import sys
from importlib.resources import files

from streamlit.web import cli as streamlit_cli


def main() -> None:
    """Run RoadLens with portable privacy and upload defaults."""
    extra_arguments = sys.argv[1:]
    app_path = files("app").joinpath("main.py")
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.headless=true",
        "--server.maxUploadSize=100",
        "--browser.gatherUsageStats=false",
        *extra_arguments,
    ]
    streamlit_cli.main()


if __name__ == "__main__":
    main()
