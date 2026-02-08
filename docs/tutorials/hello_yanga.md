# Create a Hello World Yanga Project

## Option 1: VS Code Dev Container (Recommended)

The easiest way to get started is using VS Code with the Dev Container extension. The container includes all build tools (CMake, GCC, Clang, cppcheck) and Yanga pre-installed.

1. Install [VS Code](https://code.visualstudio.com/) and the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Install [Docker Desktop](https://www.docker.com/products/docker-desktop) or [Podman](https://podman.io/)
3. Install Yanga and create a new project:

```bash
pipx install yanga
yanga init --project-dir hello_yanga
```

4. Open the `hello_yanga` folder in VS Code, then click **Reopen in Container** when prompted
5. In the container terminal, build:

```bash
yanga run
```

:::{note}
The `yanga init` command creates a project with a `.devcontainer` configuration already included.
:::

For more details about the dev container image, see [yanga-devcontainer](https://github.com/cuinixam/yanga-devcontainer).

---

## Option 2: Windows (Native)

On Windows, install Yanga with `pipx` and create a new project:

```powershell
pipx install yanga
yanga init --project-dir C:\temp\hello_yanga
cd C:\temp\hello_yanga
yanga run
```

:::{note}
The `yanga run` command will bootstrap the build environment and build the project.
:::

---

## Option 3: macOS / Linux (Native)

If you already have build tools installed (CMake, GCC or Clang), follow the same steps:

```bash
pipx install yanga
yanga init --project-dir ~/hello_yanga
cd ~/hello_yanga
yanga run
```

:::{tip}
Use `yanga --help` for a list of all available commands.
:::
