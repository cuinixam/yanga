from argparse import Namespace
from pathlib import Path

import pytest
from yanga_core.domain.execution_context import UserRequest, UserRequestScope, UserRequestTarget
from yanga_core.domain.reports import ComponentReportData, ReportData, ReportRelevantFiles, ReportRelevantFileType

from yanga.commands.gcovr import CreateVariantGcovrConfigCommand


def component(tmp_path: Path, name: str, file_type: ReportRelevantFileType) -> ComponentReportData:
    target = UserRequest(UserRequestScope.COMPONENT, variant_name="Disco", component_name=name, target=UserRequestTarget.COVERAGE)
    return ComponentReportData(files=[ReportRelevantFiles(target=target, file_type=file_type, files_to_be_included=[])], build_dir=tmp_path / name, name=name)


@pytest.mark.parametrize(
    ("file_type", "expected_lines"),
    [
        (ReportRelevantFileType.COVERAGE_RESULT, 2),
        (ReportRelevantFileType.SOURCES, 1),
    ],
    ids=["with-coverage", "without-coverage"],
)
def test_variant_config_lists_the_coverage_json_of_every_component_with_a_coverage_target(tmp_path: Path, file_type: ReportRelevantFileType, expected_lines: int) -> None:
    report_config = tmp_path / "report_config.json"
    ReportData(project_dir=tmp_path, components=[component(tmp_path, "spled", file_type)]).to_json_file(report_config)
    output_file = tmp_path / "gcovr.cfg"

    CreateVariantGcovrConfigCommand().run(Namespace(variant_report_config=report_config, output_file=output_file))

    lines = output_file.read_text().splitlines()
    assert lines[0] == f"root = {tmp_path.as_posix()}"
    assert len(lines) == expected_lines
    if expected_lines == 2:
        assert lines[1] == f"add-tracefile = {(tmp_path / 'spled' / 'coverage.json').as_posix()}"
