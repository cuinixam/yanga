"""Command line utility to create target documentation from targets data."""

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from clanguru.doc_generator import DocStructure, MarkdownFormatter, Section, TextContent
from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger

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
        """Generate HTML tree for a target and its dependencies."""
        if visited is None:
            visited = set()

        if target.name in visited:
            # For custom commands, show a reference to avoid duplication
            if target.target_type == TargetType.CUSTOM_COMMAND:
                return "<li><strong>custom command</strong> (see above)</li>"
            else:
                return f"<li><strong>{target.name}</strong> (circular dependency)</li>"

        visited.add(target.name)

        # Create the main target entry
        if target.target_type == TargetType.CUSTOM_COMMAND:
            display_name = "custom command"
        else:
            display_name = target.name

        description = f" - {target.description}" if target.description else ""
        outputs_str = f" -> [{', '.join(str(out) for out in target.outputs)}]" if target.outputs else ""

        if not target.depends:
            result = f"<li><strong>{display_name}</strong>{description}{outputs_str}</li>"
        else:
            result = f"""<li>
<details>
<summary><strong>{display_name}</strong>{description}{outputs_str}</summary>
<ul>"""

            # Group dependencies by custom command
            custom_command_deps: dict[str, dict[str, Any]] = {}  # custom_command_name -> set of output files
            regular_deps: list[str | Target] = []

            for dep_name in target.depends:
                # First try to find by target name
                dep_target = self.targets_by_name.get(str(dep_name))

                # If not found by name, try to find by output file
                if not dep_target:
                    dep_target = self.outputs_to_targets.get(str(dep_name))

                if dep_target:
                    if dep_target.target_type == TargetType.CUSTOM_COMMAND:
                        # Group this output under the custom command
                        if dep_target.name not in custom_command_deps:
                            custom_command_deps[dep_target.name] = {"target": dep_target, "outputs": set()}
                        custom_command_deps[dep_target.name]["outputs"].add(str(dep_name))
                    else:
                        regular_deps.append(dep_target)
                else:
                    regular_deps.append(str(dep_name))

            # Add grouped custom commands
            for _, cmd_info in custom_command_deps.items():
                cmd_target = cmd_info["target"]
                if cmd_target.name not in visited:
                    visited.add(cmd_target.name)
                    outputs_used = sorted(cmd_info["outputs"])
                    outputs_str = f" (uses: {', '.join(outputs_used)})" if outputs_used else ""
                    description = f" - {cmd_target.description}" if cmd_target.description else ""

                    # If the custom command has dependencies, show them in a collapsible tree
                    if cmd_target.depends:
                        result += f"""<li>
<details>
<summary><strong>custom command</strong>{description}{outputs_str}</summary>
<ul>"""
                        # Show dependencies of the custom command
                        for dep_name in cmd_target.depends:
                            # First try to find by target name
                            dep_target = self.targets_by_name.get(str(dep_name))

                            # If not found by name, try to find by output file
                            if not dep_target:
                                dep_target = self.outputs_to_targets.get(str(dep_name))

                            if dep_target:
                                result += self.generate_target_tree_html(dep_target, visited)
                            else:
                                result += f"<li>{dep_name} (external dependency)</li>"

                        result += "</ul></details></li>"
                    else:
                        result += f"<li><strong>custom command</strong>{description}{outputs_str}</li>"
                else:
                    result += "<li><strong>custom command</strong> (see above)</li>"

            # Add regular dependencies
            for dep in regular_deps:
                if isinstance(dep, str):
                    result += f"<li>{dep} (external dependency)</li>"
                else:
                    result += self.generate_target_tree_html(dep, visited)

            result += "</ul></details></li>"

        return result


class TargetDocumentationGenerator:
    """Generates documentation structure for targets using DocStructure."""

    def __init__(self, targets_data: TargetsData) -> None:
        self.targets_data = targets_data
        self.tree_builder = TargetDependencyTreeBuilder(targets_data)

    def create_doc_structure(self) -> DocStructure:
        """Create a DocStructure for target dependencies documentation."""
        doc = DocStructure("Target Dependencies Documentation")

        # Add summary section
        self._add_summary_section(doc)

        # Add root targets sections
        root_targets = self.tree_builder.find_root_targets()
        if root_targets:
            self._add_root_targets_sections(doc, root_targets)

        return doc

    def _add_summary_section(self, doc: DocStructure) -> None:
        """Add summary statistics section."""
        summary_section = Section("Summary")

        total_targets = len(self.targets_data.targets)
        root_targets = self.tree_builder.find_root_targets()

        summary_text = f"- **Total targets**: {total_targets}\n"
        summary_text += f"- **Root targets (CMakeCustomTargets only)**: {len(root_targets)}\n\n"
        summary_text += "This document provides an overview of CMake custom target dependencies. Only CMakeCustomTargets are shown as root targets."

        summary_section.add_content(TextContent(summary_text))
        doc.add_section(summary_section)

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
