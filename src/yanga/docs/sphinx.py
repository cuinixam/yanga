"""Utility functions for Sphinx documentation generation which can be used in 'conf.py'."""

import io
import json
import os
import traceback
from pathlib import Path
from typing import Any, Optional

from py_app_dev.core.exceptions import UserNotificationException

from yanga.domain.reports import ReportData


def _relativize_path(file: Path, project_dir: Path) -> str:
    return file.absolute().relative_to(project_dir).as_posix()


class SphinxReportConfig(ReportData):
    @classmethod
    def from_json_file(cls, file_path: Path) -> "SphinxReportConfig":
        try:
            result = cls.from_dict(json.loads(file_path.read_text()))
        except Exception as e:
            output = io.StringIO()
            traceback.print_exc(file=output)
            raise UserNotificationException(output.getvalue()) from e
        return result

    def _relativize_path(self, file: Path) -> str:
        return _relativize_path(file, self.project_dir)

    def create_component_myst_toc(self, component_name: str, maxdepth: int = 1, caption: Optional[str] = None) -> str:
        """Generate the myst table of contents for the component documentation."""
        content = [
            "\n```{toctree}",
            f":maxdepth: {maxdepth}\n",
        ]
        for file in self.get_component_files_list(component_name):
            content.append(f"{file}")
        content.append("```\n")
        return "\n".join(content)

    def _collect_files_from_config(self, config: Any) -> list[str]:
        """Helper method to collect and relativize file paths from a configuration object."""
        content = []
        file_attributes = ["docs_files", "test_results", "coverage_results", "lint_results", "sources", "other_files"]

        for attr in file_attributes:
            if hasattr(config, attr):
                files = getattr(config, attr)
                for file in files:
                    content.append(f"{self._relativize_path(file)}")
        return content

    def get_component_files_list(self, component_name: str) -> list[str]:
        component = next((comp for comp in self.components if comp.name == component_name), None)
        if not component:
            return []
        return self._collect_files_from_config(component)

    def get_variant_files_list(self) -> list[str]:
        if not self.variant_data:
            return []
        return self._collect_files_from_config(self.variant_data)

    @property
    def say_hello(self) -> str:
        return "Hello Sphinx!"


class SphinxConfig:
    """Configuration options for Sphinx documentation generation."""

    REPORT_CONFIGURATION_FILE_ENV_NAME = "REPORT_CONFIGURATION_FILE"

    def __init__(self) -> None:
        self.report_data = self._load_report_config_data()

    def _load_report_config_data(self) -> Optional[SphinxReportConfig]:
        report_config_file_path_str = os.environ.get(self.REPORT_CONFIGURATION_FILE_ENV_NAME, None)

        if report_config_file_path_str:
            report_config_file = Path(report_config_file_path_str)
            if report_config_file.is_file():
                return SphinxReportConfig.from_json_file(report_config_file)
        return None

    @property
    def project(self) -> str:
        return self.report_data.variant_name if self.report_data else "Unknown"

    @property
    def html_context(self) -> dict[str, Any]:
        return {"report_data": self.report_data}

    @property
    def include_patterns(self) -> list[str]:
        """Collect all files from the report config."""
        if self.report_data:
            return [_relativize_path(file, self.report_data.project_dir) for file in self.report_data.collect_all_files()]
        return []

    @staticmethod
    def render_with_jinja(app, docname, source) -> None:  # type: ignore
        """Render pages using jinja templating."""
        # Make sure we're outputting HTML
        if app.builder.format != "html":
            return
        src = source[0]
        rendered = app.builder.templates.render_string(src, app.config.html_context)
        source[0] = rendered
        return
