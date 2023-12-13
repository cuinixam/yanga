from enum import auto
from pathlib import Path
from typing import List, Optional

import customtkinter
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger, time_it
from py_app_dev.core.subprocess import SubprocessExecutor
from py_app_dev.mvp.event_manager import EventID, EventManager
from py_app_dev.mvp.presenter import Presenter
from py_app_dev.mvp.view import View

from yanga.project.project_slurper import YangaProjectSlurper
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.generators.build_system_request import (
    BuildSystemRequest,
    BuildVariantRequest,
    CleanVariantRequest,
    CompileComponentRequest,
    TestComponentRequest,
)
from yanga.ybuild.pipeline import StageRunner

from .icons import Icons


class YangaEvent(EventID):
    BUILD_EVENT = auto()
    COMPONENT_COMPILE_EVENT = auto()
    COMPONENT_TEST_EVENT = auto()
    REFRESH_EVENT = auto()
    VARIANT_SELECTED_EVENT = auto()
    CLEAN_VARIANT_EVENT = auto()
    OPEN_IN_VSCODE = auto()


class YangaView(View):
    def __init__(self, event_manager: EventManager) -> None:
        self.event_manager = event_manager
        self.root = customtkinter.CTk()
        self.variants: List[str] = []
        self.components: List[str] = []

    @property
    def selected_variant(self) -> str:
        return self.variant_selection.get()

    @property
    def selected_component(self) -> str:
        return self.component_selection.get()

    def init_gui(self) -> None:
        customtkinter.set_default_color_theme("green")

        # Configure the main window
        self.root.title("YANGA")
        self.root.geometry(f"{220}x{400}")

        # update app icon
        self.root.iconbitmap(Icons.YANGA_ICON.file)
        position_in_grid = 0

        self.variants_frame = self._create_variants_frame(self.root, position_in_grid)
        position_in_grid += 1
        self.components_frame = self._create_components_frame(self.root, position_in_grid)

        # Bind F5 key to refresh functionality
        self.root.bind("<F5>", self._refresh_button_pressed)

        # Create events
        self.build_trigger = self.event_manager.create_event_trigger(YangaEvent.BUILD_EVENT)
        self.clean_variant_trigger = self.event_manager.create_event_trigger(YangaEvent.CLEAN_VARIANT_EVENT)
        self.component_compile_trigger = self.event_manager.create_event_trigger(YangaEvent.COMPONENT_COMPILE_EVENT)
        self.component_test_trigger = self.event_manager.create_event_trigger(YangaEvent.COMPONENT_TEST_EVENT)
        self.refresh_trigger = self.event_manager.create_event_trigger(YangaEvent.REFRESH_EVENT)
        self.variant_selected_trigger = self.event_manager.create_event_trigger(YangaEvent.VARIANT_SELECTED_EVENT)
        self.open_in_vscode_trigger = self.event_manager.create_event_trigger(YangaEvent.OPEN_IN_VSCODE)

    def _build_button_pressed(self) -> None:
        self.build_trigger(self.selected_variant)

    def _refresh_button_pressed(self, event=None) -> None:  # type: ignore
        self.refresh_trigger()

    def _variant_selected(self, variant_selected: str) -> None:
        self.variant_selected_trigger(variant_selected)

    def _component_compile_button_pressed(self) -> None:
        self.component_compile_trigger(self.selected_variant, self.selected_component)

    def _component_test_button_pressed(self) -> None:
        self.component_test_trigger(self.selected_variant, self.selected_component)

    def _clean_variant_button_pressed(self) -> None:
        self.clean_variant_trigger(self.selected_variant)

    def _open_in_vscode_button_pressed(self) -> None:
        self.open_in_vscode_trigger()

    def mainloop(self) -> None:
        self.root.mainloop()

    def _create_variants_frame(self, root: customtkinter.CTk, position_in_root_grid: int) -> customtkinter.CTkFrame:
        # Create the frame for all elements related to variants
        variants_frame = customtkinter.CTkFrame(root)
        variants_frame.grid(row=position_in_root_grid, column=0, sticky="nsew", padx=10, pady=10)
        current_frame = variants_frame
        position_in_grid = 0

        # Create label aligned to left
        variants_label = customtkinter.CTkLabel(current_frame, text="Variants", anchor="w")
        variants_label.grid(row=position_in_grid, column=0, sticky="nsew", padx=10, pady=5)
        position_in_grid += 1

        # Create selection list
        self.variant_selection = customtkinter.CTkOptionMenu(current_frame, command=self._variant_selected)
        self.variant_selection.grid(row=position_in_grid, column=0, sticky="nsew", padx=10, pady=5)
        self.update_variants(self.variants)
        position_in_grid += 1

        # Create the build button
        self.build_button = customtkinter.CTkButton(current_frame, text="Build", command=self._build_button_pressed)
        self.build_button.grid(row=position_in_grid, column=0, sticky="nsew", padx=10, pady=5)
        position_in_grid += 1

        # Create the clean button
        self.clean_button = customtkinter.CTkButton(
            current_frame, text="Clean", command=self._clean_variant_button_pressed
        )
        self.clean_button.grid(row=position_in_grid, column=0, sticky="nsew", padx=10, pady=5)
        position_in_grid += 1

        # Create the open in vscode button
        self.open_in_vscode_button = customtkinter.CTkButton(
            current_frame, text="Open in VSCode", command=self._open_in_vscode_button_pressed
        )
        self.open_in_vscode_button.grid(row=position_in_grid, column=0, sticky="nsew", padx=10, pady=5)
        position_in_grid += 1

        return variants_frame

    def _create_components_frame(self, root: customtkinter.CTk, position_in_root_grid: int) -> customtkinter.CTkFrame:
        # Create the frame for all elements related to components
        components_frame = customtkinter.CTkFrame(root)
        components_frame.grid(row=position_in_root_grid, column=0, sticky="nsew", padx=10, pady=10)
        current_frame = components_frame
        position_in_grid = 0

        # Create label aligned to left
        components_label = customtkinter.CTkLabel(current_frame, text="Components", anchor="w")
        components_label.grid(row=position_in_grid, column=0, sticky="nsew", padx=10, pady=5)
        position_in_grid += 1

        # Create selection list
        self.component_selection = customtkinter.CTkOptionMenu(current_frame)
        self.component_selection.grid(row=position_in_grid, column=0, sticky="nsew", padx=10, pady=5)

        position_in_grid += 1

        # Create component compile button
        self.component_compile_button = customtkinter.CTkButton(
            current_frame, text="Compile", command=self._component_compile_button_pressed
        )
        self.component_compile_button.grid(row=position_in_grid, column=0, sticky="nsew", padx=10, pady=5)
        position_in_grid += 1

        # Create component test button
        self.component_test_button = customtkinter.CTkButton(
            current_frame, text="Test", command=self._component_test_button_pressed
        )
        self.component_test_button.grid(row=position_in_grid, column=0, sticky="nsew", padx=10, pady=5)
        position_in_grid += 1

        return components_frame

    def update_variants(self, variants: List[str]) -> None:
        self.variant_selection.configure(values=variants)

    def update_current_variant(self, variant: str) -> None:
        self.variant_selection.set(variant)

    def enable_variant_commands(self) -> None:
        self.build_button.configure(state="normal")
        self.clean_button.configure(state="normal")

    def disable_variant_commands(self) -> None:
        self.build_button.configure(state="disabled")
        self.clean_button.configure(state="disabled")

    def update_components(self, components: List[str]) -> None:
        self.component_selection.configure(values=components)

    def update_current_component(self, component: str) -> None:
        self.component_selection.set(component)

    def enable_component_commands(self) -> None:
        self.component_compile_button.configure(state="normal")

    def disable_component_commands(self) -> None:
        self.component_compile_button.configure(state="disabled")


class YangaPresenter(Presenter):
    def __init__(self, view: YangaView, event_manager: EventManager, project_dir: Path) -> None:
        self.logger = logger.bind()
        self.view = view
        self.event_manager = event_manager
        self.project_dir = project_dir
        self.project = self._create_project()
        self.event_manager.subscribe(YangaEvent.BUILD_EVENT, self._build_trigger)
        self.event_manager.subscribe(YangaEvent.COMPONENT_COMPILE_EVENT, self._component_compile_trigger)
        self.event_manager.subscribe(YangaEvent.COMPONENT_TEST_EVENT, self._test_compile_trigger)
        self.event_manager.subscribe(YangaEvent.REFRESH_EVENT, self._refresh_trigger)
        self.event_manager.subscribe(YangaEvent.VARIANT_SELECTED_EVENT, self._variant_selected_trigger)
        self.event_manager.subscribe(YangaEvent.CLEAN_VARIANT_EVENT, self._clean_variant_trigger)
        self.event_manager.subscribe(YangaEvent.OPEN_IN_VSCODE, self._open_in_vscode_trigger)
        self.command_running_flag = False
        self.running_build_system_request: Optional[BuildSystemRequest] = None
        self.selected_variant: Optional[str] = None
        self.selected_component: Optional[str] = None

    def run(self) -> None:
        self.view.init_gui()
        self._update_view_data()
        self.view.mainloop()

    def _build_trigger(self, variant_name: str) -> None:
        self.run_command(BuildVariantRequest(variant_name))

    def _component_compile_trigger(self, variant_name: str, component_name: str) -> None:
        self.run_command(CompileComponentRequest(variant_name, component_name))

    def _test_compile_trigger(self, variant_name: str, component_name: str) -> None:
        self.run_command(TestComponentRequest(variant_name, component_name))

    def _refresh_trigger(self) -> None:
        self.project = self._create_project()
        self._update_view_data()

    def _variant_selected_trigger(self, variant_name: str) -> None:
        self.logger.info(f"Variant selected: {variant_name}")
        self.selected_variant = variant_name
        self._update_components()

    def _clean_variant_trigger(self, variant_name: str) -> None:
        self.run_command(CleanVariantRequest(variant_name))

    def _open_in_vscode_trigger(self) -> None:
        if not self.project:
            self.logger.warning("Project is not loaded")
            return
        self.logger.info("Opening project in VSCode")
        try:
            SubprocessExecutor(["code", self.project_dir.as_posix()], shell=True).execute()  # nosec
        except UserNotificationException as e:
            self.logger.error(e)

    def _update_view_data(self) -> None:
        self._update_variants()
        self._update_components()

    def _update_variants(self) -> None:
        variants = []
        if self.project:
            variants = [variant.name for variant in self.project.variants]
        if variants:
            variants.sort()
            self.selected_variant = variants[0]
        else:
            variants = ["No variants found"]
            self.selected_variant = None
        self.view.update_variants(variants)
        self.view.update_current_variant(variants[0])
        if self.selected_variant:
            self.view.enable_variant_commands()
        else:
            self.view.disable_variant_commands()

    def _update_components(self) -> None:
        components = []
        if self.project and self.selected_variant:
            components = self._create_component_names(self.selected_variant)
        if components:
            components.sort()
            self.selected_component = components[0]
        else:
            components = ["No components found"]
            self.selected_component = None
        self.view.update_components(components)
        self.view.update_current_component(components[0])
        if self.selected_component:
            self.view.enable_component_commands()
        else:
            self.view.disable_component_commands()

    @time_it("executing command")
    def run_command(self, build_system_request: BuildSystemRequest) -> None:
        # Make sure the project is loaded before running any command.
        # Otherwise, there might be configuration changes that are not reflected in the project.
        self.project = self._create_project()
        if not self.project:
            self.logger.warning("Project is not loaded")
            return
        if self.command_running_flag:
            self.logger.warning(
                f"Command '{self.running_build_system_request}' still running. Skip starting new command."
            )
            return
        if not self.selected_variant:
            UserNotificationException("No variant selected. This looks like a bug.")
        self.logger.info(f"Selected variant: {build_system_request.variant_name}")
        if build_system_request.component_name:
            self.logger.info(f"Selected component: {build_system_request.component_name}")
        self.logger.info(f"Selected command: {build_system_request.command}")
        self.command_running_flag = True
        self.running_build_system_request = build_system_request
        try:
            build_environment = BuildEnvironment(
                self.project_dir,
                build_system_request,
                self.project.get_variant_components(build_system_request.variant_name),
                self.project.user_config_files,
                self.project.get_variant_config_file(build_system_request.variant_name),
            )
            for stage in self.project.stages:
                StageRunner(build_environment, stage).run()
        except UserNotificationException as e:
            self.logger.error(e)
        finally:
            self.command_running_flag = False
            self.running_build_system_request = None

    def _create_project(self) -> Optional[YangaProjectSlurper]:
        try:
            return YangaProjectSlurper(self.project_dir)
        except UserNotificationException as e:
            self.logger.error(e)
            return None

    def _create_component_names(self, variant_name: str) -> List[str]:
        if self.project:
            try:
                components = self.project.get_variant_components(variant_name)
                return [component.name for component in components]
            except UserNotificationException as e:
                self.logger.error(e)
                return []
        return []


class YangaGui:
    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.logger = logger.bind()

    def run(self) -> None:
        try:
            event_manager = EventManager()
            view = YangaView(event_manager)
            presenter = YangaPresenter(view, event_manager, self.project_dir)
            presenter.run()
        except UserNotificationException as e:
            self.logger.error(e)
