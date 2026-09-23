"""Project-root conftest: load the plugin under coverage and enable pytester.

The entry-point autoload is disabled in addopts (`-p no:resources`) so this explicit
load happens once coverage is already tracing. Subprocess (pytester) runs use their
own rootdir and load the plugin through the entry point as a real consumer would.
"""

pytest_plugins = ["pytest_resources.plugin", "pytester"]
