Usage
#####

Setup a new project
===================

To setup a new project, you need to run ``yanga init`` in the root directory of your project.
This will create the necessary files to get you started with an ``Hello World`` project.

Build a project
---------------

There are two scripts to build a project:

* `build.ps1` this is the main script for windows. It only makes sure the correct Python version is installed and then calls the `build.py` script. We decided to implement as less as possible in PowerShell, because this is available only on Windows hosts.
* `build.py` platform agnostic script. This script is called by `build.ps1` and `build.sh` and does the actual work. It is written in Python, because this is available on all platforms.


Steps to bootstrap a project and call ``yanga``:

* check if the required Python version is installed
* if not, install it using scoop
* if scoop not installed, install it first and then install Python
* as soon as Python is installed, call `build.py` to continue the setup
    * Check which python package manager is required
        * if there is a pipfile or requirements.txt, use pipenv
        * if there is project.toml, use poetry
    * Run pip to install the package manager
    * Run the package manager to install the dependencies
    * Start the build system (e.g. ``yanga``) using the package manager to make sure the correct environment is used (e.g. ``pipenv run yanga build``).
