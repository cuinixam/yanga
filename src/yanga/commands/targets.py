"""Command line utility to create target documentation from targets data."""

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from clanguru.doc_generator import DocStructure, MarkdownFormatter, Section, TextContent
from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger, time_it

from yanga.cmake.generator import GeneratedFile
from yanga.domain.config import BaseConfigJSONMixin
from yanga.domain.targets import Target, TargetsData, TargetType

from .base import create_config


class TargetDependencyTreeBuilder:
    """Builds and analyzes target dependency trees."""

    def __init__(self, targets_data: TargetsData) -> None:
        self.targets_data = targets_data
        self.targets_by_name = {target.name: target for target in targets_data.targets}
        # Create a mapping from output files to the targets that produce them
        self.outputs_to_targets = {}
        for target in targets_data.targets:
            for output in target.outputs:
                self.outputs_to_targets[str(output)] = target

    def find_root_targets(self) -> list[Target]:
        """Find targets that are not dependencies of any other target and are CMakeCustomTargets."""
        all_dependencies: set[str] = set()
        for target in self.targets_data.targets:
            all_dependencies.update(str(dep) for dep in target.depends)

        root_targets = []
        for target in self.targets_data.targets:
            # Only include CMakeCustomTargets as root targets and exclude those that are dependencies
            if target.name not in all_dependencies and target.target_type == TargetType.CUSTOM_TARGET:
                root_targets.append(target)

        return root_targets

    def generate_target_tree_html(self, target: Target, visited: set[str] | None = None) -> str:
        """
        Generate HTML tree for a target and its dependencies.

        Optimized to minimize string concatenation overhead by using list appends
        and joining at the end (significant when documenting many targets).
        """
        if visited is None:
            visited = set()

        if target.name in visited:
            if target.target_type == TargetType.CUSTOM_COMMAND:
                return "<li><strong>custom command</strong> (see above)</li>"
            return f"<li><strong>{target.name}</strong> (circular dependency)</li>"

        visited.add(target.name)

        display_name = "custom command" if target.target_type == TargetType.CUSTOM_COMMAND else target.name
        description = f" - {target.description}" if target.description else ""
        outputs_str = f" -> [{', '.join(str(out) for out in target.outputs)}]" if target.outputs else ""

        # Fast path: no dependencies
        if not target.depends:
            return f"<li><strong>{display_name}</strong>{description}{outputs_str}</li>"

        parts: list[str] = [
            "<li>",
            "<details>",
            f"<summary><strong>{display_name}</strong>{description}{outputs_str}</summary>",
            "<ul>",
        ]

        custom_command_deps: dict[str, dict[str, Any]] = {}
        regular_deps: list[str | Target] = []

        for dep_name in target.depends:
            dep_name_str = str(dep_name)
            dep_target = self.targets_by_name.get(dep_name_str) or self.outputs_to_targets.get(dep_name_str)

            if dep_target:
                if dep_target.target_type == TargetType.CUSTOM_COMMAND:
                    info = custom_command_deps.setdefault(dep_target.name, {"target": dep_target, "outputs": set()})
                    info["outputs"].add(dep_name_str)
                else:
                    regular_deps.append(dep_target)
            else:
                regular_deps.append(dep_name_str)

        # Add grouped custom commands
        for cmd_info in custom_command_deps.values():
            cmd_target: Target = cmd_info["target"]
            if cmd_target.name in visited:
                parts.append("<li><strong>custom command</strong> (see above)</li>")
                continue
            visited.add(cmd_target.name)
            outputs_used = sorted(cmd_info["outputs"])
            outputs_used_str = f" (uses: {', '.join(outputs_used)})" if outputs_used else ""
            cmd_description = f" - {cmd_target.description}" if cmd_target.description else ""
            if cmd_target.depends:
                parts.extend(["<li>", "<details>", f"<summary><strong>custom command</strong>{cmd_description}{outputs_used_str}</summary>", "<ul>"])
                for dep_name in cmd_target.depends:
                    dep_name_str = str(dep_name)
                    dep_dep_target = self.targets_by_name.get(dep_name_str) or self.outputs_to_targets.get(dep_name_str)
                    if dep_dep_target:
                        parts.append(self.generate_target_tree_html(dep_dep_target, visited))
                    else:
                        parts.append(f"<li>{dep_name} (external dependency)</li>")
                parts.append("</ul></details></li>")
            else:
                parts.append(f"<li><strong>custom command</strong>{cmd_description}{outputs_used_str}</li>")

        # Add regular dependencies
        for dep in regular_deps:
            if isinstance(dep, str):
                parts.append(f"<li>{dep} (external dependency)</li>")
            else:
                parts.append(self.generate_target_tree_html(dep, visited))

        parts.append("</ul></details></li>")
        return "".join(parts)


class TargetDocumentationGenerator:
    """Generates documentation structure for targets using DocStructure."""

    def __init__(self, targets_data: TargetsData) -> None:
        self.targets_data = targets_data
        self.tree_builder = TargetDependencyTreeBuilder(targets_data)

    def create_doc_structure(self) -> DocStructure:
        """
        Create a DocStructure for target dependencies documentation.

        Optimizations:
        - Compute root targets once (was computed twice).
        - Pass pre-computed root targets to summary section.
        """
        doc = DocStructure("Target Dependencies Documentation")
        root_targets = self.tree_builder.find_root_targets()
        self._add_summary_section(doc, root_targets)
        if root_targets:
            self._add_root_targets_sections(doc, root_targets)
        return doc

    def _add_summary_section(self, doc: DocStructure, root_targets: list[Target]) -> None:
        """Add summary statistics section using pre-computed root targets."""
        total_targets = len(self.targets_data.targets)
        summary_text = (
            f"- **Total targets**: {total_targets}\n"
            f"- **Root targets (CMakeCustomTargets only)**: {len(root_targets)}\n\n"
            "This document provides an overview of CMake custom target dependencies. Only CMakeCustomTargets are shown as root targets."
        )
        section = Section("Summary")
        section.add_content(TextContent(summary_text))
        doc.add_section(section)

    def _add_root_targets_sections(self, doc: DocStructure, root_targets: list[Target]) -> None:
        """Add sections for each root target with dependency trees."""
        root_targets_section = Section("Root Targets (CMakeCustomTargets)")
        root_targets_section.add_content(TextContent("These are the main CMakeCustomTargets that are not dependencies of other targets."))

        for target in root_targets:
            target_section = self._create_target_section(target)
            root_targets_section.add_subsection(target_section)

        doc.add_section(root_targets_section)

    def _create_target_section(self, target: Target) -> Section:
        """Create a section for a single target with its information and dependency tree."""
        target_section = Section(target.name)

        # Add target description
        if target.description:
            target_section.add_content(TextContent(f"**Description**: {target.description}"))

        # Add target outputs
        if target.outputs:
            outputs_list = ", ".join(f"`{out}`" for out in target.outputs)
            target_section.add_content(TextContent(f"**Outputs**: {outputs_list}"))

        # Add dependency tree
        dependency_tree_html = self.tree_builder.generate_target_tree_html(target)
        if dependency_tree_html:
            tree_content = f"**Dependency Tree**:\n\n<ul>\n{dependency_tree_html}\n</ul>"
            target_section.add_content(TextContent(tree_content))

        return target_section


def create_doc_structure(targets_data: TargetsData, title: str = "Target Dependencies Documentation") -> DocStructure:
    """Utility function to create a DocStructure for targets documentation."""
    generator = TargetDocumentationGenerator(targets_data)
    doc_structure = generator.create_doc_structure()
    doc_structure.title = title
    return doc_structure


@dataclass
class CommandArgs(BaseConfigJSONMixin):
    variant_targets_data_file: Path = field(metadata={"help": "Variant targets data JSON file."})
    output_file: Path = field(metadata={"help": "Output targets data documentation file."})


class TargetsDocCommand(Command):
    def __init__(self) -> None:
        super().__init__("targets_doc", "Create a variant targets data documentation file with collapsible dependency trees.")
        self.logger = logger.bind()

    @time_it("targets_doc command")
    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        cmd_args = create_config(CommandArgs, args)
        targets_data = TargetsData.from_json_file(cmd_args.variant_targets_data_file)
        content = MarkdownFormatter().format(create_doc_structure(targets_data))
        GeneratedFile(cmd_args.output_file, content).to_file()
        self.logger.info(f"Generated target documentation at {cmd_args.output_file}")
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, CommandArgs)
