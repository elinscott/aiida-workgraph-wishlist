"""Sphinx configuration for the aiida-workgraph wishlist page."""

from docutils import nodes

project = "aiida-workgraph wishlist"
extensions = ["sphinx_design"]
html_theme = "furo"
html_title = project
exclude_patterns = ["_build"]


def strip_trailing_blank_lines(app, doctree):
    """Drop the blank lines an example region keeps before its end marker."""
    for block in doctree.findall(nodes.literal_block):
        text = block.astext()
        if text.endswith("\n"):
            text = text.rstrip("\n")
            block.rawsource = text
            block.children = [nodes.Text(text)]


def setup(app):
    """Register the literal-block cleanup."""
    app.connect("doctree-read", strip_trailing_blank_lines)
