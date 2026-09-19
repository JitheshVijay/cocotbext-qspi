"""Sphinx configuration."""

import importlib.metadata

project = "cocotbext-qspi"
author = "Jithesh Vijay"
copyright = "2026, Jithesh Vijay"

try:
    release = importlib.metadata.version("cocotbext-qspi")
except importlib.metadata.PackageNotFoundError:
    # Building from a checkout without the package installed.
    release = "0.2.0"
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "myst_parser",
]

# The README is the front page, so it does not have to be written twice and
# cannot drift from what people see on GitHub and PyPI.
myst_enable_extensions = ["colon_fence", "deflist"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "cocotb": ("https://docs.cocotb.org/en/stable/", None),
}

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

html_theme = "furo"
html_title = "cocotbext-qspi {}".format(release)
templates_path = []
exclude_patterns = ["_build", "waveforms"]


def _sync_readme(app):
    """Copy the README into docs/ with its image paths rebased.

    The README uses repo-relative paths so the images render on GitHub and
    PyPI. Included from inside docs/, those paths do not resolve -- so
    rewrite them here rather than keeping a second copy that drifts.
    """
    from pathlib import Path

    here = Path(__file__).parent
    text = (here.parent / "README.md").read_text()
    text = text.replace("](docs/waveforms/", "](waveforms/")
    (here / "readme.md").write_text(
        "<!-- Generated from ../README.md by conf.py; do not edit. -->\n\n"
        + text
    )


def setup(app):
    app.connect("builder-inited", lambda _: _sync_readme(app))
