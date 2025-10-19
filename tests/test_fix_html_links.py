"""Test the fix_html_links command."""

from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory

from yanga.commands.fix_html_links import FixHtmlLinksCommand


def test_fix_html_links_command() -> None:
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test HTML files with buggy links
        (temp_path / "subdir").mkdir()

        # Root level file
        root_html = temp_path / "index.html"
        root_html.write_text('<a href="./docs/guide.html#http://">Guide</a>\n<a href="./api/index.html#http://">API</a>')

        # Subdirectory file
        sub_html = temp_path / "subdir" / "page.html"
        sub_html.write_text('<a href="./docs/guide.html#http://">Guide</a>\n<a href="./api/reference.html#http://">Reference</a>')

        # File without buggy links (should remain unchanged)
        clean_html = temp_path / "clean.html"
        clean_html.write_text('<a href="normal-link.html">Normal</a>')

        # Create command and run it
        command = FixHtmlLinksCommand()

        # Create proper argparse namespace
        args = Namespace(report_dir=temp_path, verbose=False)

        result = command.run(args)

        assert result == 0

        # Verify fixes
        root_content = root_html.read_text()
        assert 'href="docs/guide.html"' in root_content
        assert 'href="api/index.html"' in root_content
        assert "#http://" not in root_content

        sub_content = sub_html.read_text()
        assert 'href="../docs/guide.html"' in sub_content
        assert 'href="../api/reference.html"' in sub_content
        assert "#http://" not in sub_content

        # Clean file should be unchanged
        clean_content = clean_html.read_text()
        assert clean_content == '<a href="normal-link.html">Normal</a>'


def test_fix_html_links_verbose() -> None:
    """Test that verbose mode provides detailed logging."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        html_file = temp_path / "test.html"
        html_file.write_text('<a href="./docs/guide.html#http://">Guide</a>')

        command = FixHtmlLinksCommand()

        # Create proper argparse namespace with verbose enabled
        args = Namespace(report_dir=temp_path, verbose=True)

        result = command.run(args)

        assert result == 0
