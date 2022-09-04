"""CLI tool to detect issues."""

import sys
import os
import re

import fire

from rich import print as rprint

from i12r.issue_manager import IssueManager


# TODO Use default logging system
def _eprint(string: str):
    """Rich print to STDERR."""
    rprint(string, file=sys.stderr)


def _get_files(path: str):
    """Generate paths for files in selected directory."""
    if os.path.isfile(path):
        yield os.path.join(path)

    if os.path.isdir(path):
        for root, _dirs, files in os.walk(path, followlinks=False):
            for file in files:
                yield os.path.join(root, file)


def _print_result(result_dict: dict, machine_readable: bool = False):
    if machine_readable:
        rprint(result_dict)

    else:
        for file, issues in result_dict.items():
            if issues:
                file = f"[purple]{file}[/purple]"

                for issue in issues:
                    level = f"[bold blue]{issue['level']}[/bold blue]"
                    lines = (
                        f"[blue]{issue['line_start']}:{issue['line_end']}[/blue]"
                        if issue["line_start"] != issue["line_end"]
                        else f"[blue]{issue['line_start']}[/blue]"
                    )
                    content = f"{issue['content']}"

                    rprint(f"{level}\t{file}:{lines}\n{content}")

                    print("")


def cli_entrypoint(
    *args,
    debug: bool = False,
    include: str = r"",
    exclude: str = r"\./\.git/",
    json: bool = False,
):
    r"""CLI entrypoint.

    :param args: Paths to scan for files. Defaults to "./".

    :param include: Regex to include only matching paths, e.g.: ".+\.cpp$", ".+\.(py|md)$".
        Defaults to empty string.

    :param exclude: Regex to exclude matching paths from found ones, e.g.: "/dist/".
        Defaults to "\./\.git/".

    :param debug: Set to enable debug output (as standard error stream).
    :param json: Set to enable JSON machine-readable output.
    """
    if not args:
        args = ("./",)

    if debug:
        _eprint(f"# Working with paths: {args}")
        _eprint(f"# Include only: [green]{include}[/green]")
        _eprint(f"# Exclude from: [green]{exclude}[/green]")

    files = []
    for path in args:
        files.extend(_get_files(path))

    # Include only paths which match at least 1 include regex
    if include:
        files = filter(lambda x: bool(re.search(include, x)), files)

    # Exclude paths which matches at least 1 exclude regex
    files = filter(lambda x: not bool(re.search(exclude, x)), files)

    files = list(files)

    if debug:
        _eprint(f"# Found files: {len(files)}")

    i12r = IssueManager()

    result_dict = {}

    for file in files:
        # TODO Skip non-text mime-types
        # TODO Process errors e.g. missing symlinks, non-text file contents
        with open(file, encoding="utf-8") as file_:
            data = file_.read()

        issues = list(i12r.find(file, data))

        result_dict[file] = [issue.dict(exclude={"fname"}, exclude_defaults=True) for issue in issues]

    _print_result(result_dict, json)


if __name__ == "__main__":
    # TODO Get include/exclude from global config
    # TODO Get include/exclude from in-repository config

    fire.Fire(cli_entrypoint)
