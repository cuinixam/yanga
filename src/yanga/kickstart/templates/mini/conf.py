import datetime

day = datetime.date.today()
# meta data #################################################################

project = "My Project"
copyright = f"{day.year} our team"
release = f"{day}"

exclude_patterns = [
    "build",
    ".venv",
    ".git",
]

include_patterns = ["index.md"]

html_title = f"{project} {release}"
html_show_sourcelink = True

extensions = []

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
