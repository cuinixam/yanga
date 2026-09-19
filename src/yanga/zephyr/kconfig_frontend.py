"""
Zephyr Kconfig frontend that persists what the user selects.

Zephyr's own ``menuconfig``/``guiconfig`` targets edit the build's ``.config``, which a pristine
build throws away; the documentation tells the user to copy settings into a ``*.conf`` file by hand
(``doc/build/kconfig/menuconfig.rst``). This frontend does that copying: it opens the same editor and
then writes what changed into the selection file yanga declared for this variant and platform.

``yanga.zephyr.steps.ZephyrBuild`` registers it with Zephyr's ``EXTRA_KCONFIG_TARGETS`` hook (``cmake/modules/kconfig.cmake``),
so Zephyr runs it with the Kconfig environment its configure computed and the Kconfig root as argument.
``ZephyrFeatures`` runs that target and passes the selection file and the editor choice through the
environment, ``SPL_FEATURE_SELECTION`` and ``SPL_FEATURE_GUI``:

    python kconfig_frontend.py <KCONFIG_ROOT>
"""

import argparse
import importlib
import os
import re
import sys
from pathlib import Path


def merge_into(selection_file: Path, prefix: str, changed: dict[str, str]) -> str:
    """The file's own lines with the changed symbols replaced, so untouched settings keep their place."""
    assignment = re.compile(rf"^(?:# )?{re.escape(prefix)}([A-Za-z0-9_]+)(?:=| is not set)")
    lines = selection_file.read_text().splitlines(keepends=True) if selection_file.exists() else []
    kept = []
    for line in lines:
        match = assignment.match(line)
        replacement = changed.pop(match.group(1), None) if match else None
        kept.append(replacement if replacement else line)
    return "".join(kept) + "".join(changed.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="Kconfig root, appended by Zephyr's Kconfig target")
    args = parser.parse_args()
    selection = Path(os.environ["SPL_FEATURE_SELECTION"])
    gui = os.environ.get("SPL_FEATURE_GUI", "1") == "1"

    # Zephyr's tree needs Zephyr's own kconfiglib fork: it adds Kconfig syntax (configdefault) that
    # the PyPI package does not parse. Its editors live next to it.
    sys.path.insert(0, str(Path(os.environ["ZEPHYR_BASE"]) / "scripts" / "kconfig"))
    kconfiglib = importlib.import_module("kconfiglib")

    kconf = kconfiglib.Kconfig(str(args.model))
    kconf.load_config()
    before = {sym.name: sym.str_value for sym in kconf.unique_defined_syms}
    importlib.import_module("guiconfig" if gui else "menuconfig").menuconfig(kconf)
    # The editor may hold changes the user chose not to save; reloading KCONFIG_CONFIG keeps only what it wrote.
    kconf.load_config()
    # The check kconfiglib's write_min_config makes: a symbol without a prompt, or one a 'select'
    # already forces, cannot be assigned in a fragment, and Zephyr's merge rejects it. That is what
    # keeps the promptless and devicetree-derived symbols out of the selection file.
    changed = {
        sym.name: sym.config_string
        for sym in kconf.unique_defined_syms
        if (sym.choice or sym.visibility > kconfiglib.expr_value(sym.rev_dep)) and sym.str_value != before[sym.name]
    }
    if not changed:
        print(f"No change saved, {selection} left as it is.")
        return 0
    selection.write_text(merge_into(selection, kconf.config_prefix, dict(changed)))
    print(f"Wrote {len(changed)} change(s) into {selection}:")
    for line in changed.values():
        print(f"  {line.rstrip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
