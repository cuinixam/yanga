import sys
from pathlib import Path
from typing import Optional

import typer
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger, setup_logger, time_it

from yanga import __version__
from yanga.commands.init import YangaInit
from yanga.commands.run import RunCommand, RunCommandConfig
from yanga.gui import YangaGui

package_name = "yanga"

app = typer.Typer(name=package_name, help="YANGA command line interface.", no_args_is_help=True)


@app.callback(invoke_without_command=True)
def version(
    version: bool = typer.Option(None, "--version", "-v", is_eager=True, help="Show version and exit."),
) -> None:
    if version:
        typer.echo(f"{package_name} {__version__}")
        raise typer.Exit()


@app.command()
@time_it("init")
def init(
    project_dir: Path = typer.Option(Path.cwd().absolute(), help="The project directory"),  # noqa: B008
    bootstrap: bool = typer.Option(False, help="Initialize only the bootstrap files."),
) -> None:
    YangaInit(project_dir, bootstrap).run()


@app.command()
@time_it("run")
def run(
    project_dir: Path = typer.Option(Path.cwd().absolute(), help="The project directory"),  # noqa: B008,
    platform: Optional[str] = typer.Option(
        None,
        help="Platform for which to build (see the available platforms in the configuration).",
    ),
    variant_name: Optional[str] = typer.Option(
        None,
        help="SPL variant name. If none is provided, it will prompt to select one.",
    ),
    component_name: Optional[str] = typer.Option(
        None,
        help="Restrict the scope to one specific component.",
    ),
    target: Optional[str] = typer.Option(
        None,
        help="Define a specific target to execute.",
    ),
    step: Optional[str] = typer.Option(
        None,
        help="Name of the step to run (as written in the pipeline config).",
    ),
    single: bool = typer.Option(
        False,
        help="If provided, only the provided step will run, without running all previous steps in the pipeline.",
        is_flag=True,
    ),
    print: bool = typer.Option(
        False,
        help="Print the pipeline steps.",
        is_flag=True,
    ),
    force_run: bool = typer.Option(
        False,
        help="Force the execution of a step even if it is not dirty.",
        is_flag=True,
    ),
) -> None:
    RunCommand().do_run(
        RunCommandConfig(
            project_dir,
            platform,
            variant_name,
            component_name,
            target,
            step,
            single,
            print,
            force_run,
        )
    )


@app.command()
@time_it("gui")
def gui(
    project_dir: Path = typer.Option(Path.cwd().absolute(), help="The project directory"),  # noqa: B008
) -> None:
    YangaGui(project_dir).run()


def main() -> int:
    try:
        setup_logger()
        app()
        return 0
    except UserNotificationException as e:
        logger.error(f"{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
