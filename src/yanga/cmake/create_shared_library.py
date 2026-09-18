from yanga.cmake.cmake_backend import CMakeAddLibrary, CMakeElement, CMakeSetTargetProperties, CMakeTargetLinkLibraries, LibraryType
from yanga.cmake.create_executable import CreateExecutableCMakeGenerator


class CreateSharedLibraryCMakeGenerator(CreateExecutableCMakeGenerator):
    """
    Links the variant's component libraries into a shared library instead of an executable.

    For a host that loads the variant, a Python GUI through ctypes for example. The file is named
    like the executable would be, `Disco.so`/`Disco.dylib`/`Disco.dll`, no `lib` prefix, so a
    loader looks it up by variant name on every OS. Everything else is inherited.
    """

    @property
    def executable_target_name(self) -> str:
        return CMakeAddLibrary("${PROJECT_NAME}", type=LibraryType.SHARED).target_name

    def create_executable_elements(self, component_library_targets: list[str]) -> list[CMakeElement]:
        target = self.executable_target_name
        return [
            CMakeAddLibrary("${PROJECT_NAME}", type=LibraryType.SHARED),
            CMakeTargetLinkLibraries(target, component_library_targets),
            CMakeSetTargetProperties(
                target,
                {
                    "OUTPUT_NAME": "${PROJECT_NAME}",
                    "PREFIX": '""',
                    # A DLL exports nothing unless asked; .so and .dylib export by default.
                    "WINDOWS_EXPORT_ALL_SYMBOLS": "ON",
                },
            ),
        ]
