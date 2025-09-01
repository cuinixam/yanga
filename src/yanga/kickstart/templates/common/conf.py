import datetime
from typing import Any

from yanga.docs.sphinx import SphinxConfig

day = datetime.date.today()

copyright = f"{day.year} our team"
version = f"{day.year}.{day.month}.{day.day}"
release = f"{day}"

exclude_patterns = [
    ".venv",
    ".git",
]

html_context: dict[str, Any] = {
    "env": {
        # Add current execution time in UTC
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    }
}

include_patterns = [
    "index.md",
]

report_config = SphinxConfig()
html_context.update(report_config.html_context)
include_patterns.extend(report_config.include_patterns)

project = report_config.project

html_title = f"{project} {release}"
html_show_sourcelink = True

extensions = []

# Use the whole page width
extensions.append("sphinx_rtd_size")
sphinx_rtd_size_width = "90%"

# Parse markdown files
extensions.append("myst_parser")
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "html_image",
]

# The suffix of source filenames.
source_suffix = [
    ".md",
    ".rst",
]


def setup(app):  # type: ignore
    app.connect("source-read", report_config.render_with_jinja)
