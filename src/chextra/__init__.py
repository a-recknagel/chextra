"""
Some Extra Help
---------------

Given that extras are not all that common in most projects, this package offers some help
to developers and users who are trying to call code that is gated by one.
---
"""
import functools
import importlib.metadata
import importlib.resources
import inspect
import re
import warnings
from importlib import metadata

from packaging.requirements import Requirement

__version__ = metadata.version("chextra")
__all__ = ["warn"]


@functools.cache
def dependencies_grouped_by_extra(pkg: str) -> dict[str, list[str]]:
    """Collect all required dependencies.

    Note that this function does not inspect the current python environment, it only
    checks the installation metadata. In other words, it doesn't find what _is_ installed
    here, only what _should be_, and why.

    Dependencies that have no extra are collected under the empty string.

    Args:
        pkg: Name of the inspected distribution.

    Returns:
        All dependencies of the supplied distribution grouped by their extra, or `""` if
            they have none.

    Raises:
        importlib.metadata.PackageNotFoundError: If the supplied package name does not
            identify a currently installed package.
    """

    meta = importlib.metadata.metadata(pkg).json
    keys = ["", *meta.get("provides_extra", [])]
    extra_map: dict[str, list[str]] = {key: [] for key in keys}
    for req in map(Requirement, meta["requires_dist"]):
        if req.marker is None or not (
            extras := {e[2].value for e in req.marker._markers if e[0].value == "extra"}
        ):
            extra_map[""].append(req.name)
            continue
        for extra in map(_normalize_extra, extras):
            extra_map[extra].append(req.name)

    return extra_map


def _normalize_extra(extra):
    """Convert an arbitrary string to a standard 'extra' name.

    Following the spec as defined in https://peps.python.org/pep-0685/#specification.
    """
    return re.sub(r"[-_.]+", "-", extra).lower()


def _call_path(*, level: int) -> list[str]:
    """Look at the callstack's level and pick out the calling module's name."""
    call_stack = inspect.stack()
    call_frame = call_stack[level][0]
    module = inspect.getmodule(call_frame)
    if not module or module.__name__ is None:
        return []
    return module.__name__.split(".")


def warn(
    pkg: str | None = None,
    extras: str | list[str] | None = None,
    *,
    eager: bool = False,
):
    """Raise a `Warning` if a user imports a package relying on uninstalled extras.

    Call this function in the `__init__.py` of a sub-package which contains code that
    relies on an extra being installed. In order to be reachable, it must be executed
    before any third party package imports take place. Any subsecuent `ImportError`s will
    still be raised, the warning merely tries to give users a hint why their code might be
    failing.

    Given the following package structure:

    ```text
    foo
    ├── __init__.py
    └── bar
        ├── __init__.py
        └── code.py
    ```
    and `foo/bar/code.py` containing a 3rd party package import `baz` defined in the
    extra `bar`, you'd put these two lines into `foo/bar/__init__.py`:

    ``` py
    import chextra
    chextra.warn("foo", "bar")
    ```

    with `foo` being the name of your distribution and `bar` the name of the extra.

    If the third parameter, `eager`, is left in its default of `False` and a user
    only installed `foo` and not `foo[bar]`, the following will happen

    ``` py
    >>> import foo.bar       # prints a UserWarning telling to install foo[bar]
    >>> import foo.bar.code  # raise an ImportError on "baz" not being installed
    ```

    If `eager` were set to `True`, the first line would have raised an ImportError for
    `baz` already.

    In this particular example, it would also be possible to call `chextra.warn`
    without any parameters:

    ``` py
    import chextra
    chextra.warn()
    ```

    By inspecting the callstack, guessing the distribution name is under normal
    circumstances straight forward. For the name of the extra, it is not unusual to
    call the sub-package the same as the extra, so that name can be guessed from the
    context here as well. It is safe to use when your package was installed properly,
    but might be a hassle if your dev-environment or test setup executes your files
    directly instead.

    Args:
        pkg: Name of the installable distribution.
        extras: Name of the extra this call should be guarding against. Can specify
            multiple as a list.
        eager: If set to `True`, manually raise an ImportError listing missing 3rd party
            packages.
    """
    # get all prerequisites in order
    caller = _call_path(level=2)
    if pkg is None and caller != []:
        pkg, *_ = caller  # TODO: test with namespaces
    if extras is None and caller != []:
        *_, extras = caller
    if pkg is None or pkg == "__main__" or extras is None:
        warnings.warn(
            "Can't guess the package or extras if executing as a script and not calling "
            "from a module, please set them both manually.",
            stacklevel=2,
        )
        return
    if isinstance(extras, str):
        extras = [extras]
    extras = [_normalize_extra(extra) for extra in extras]

    # find out if extras are missing
    missing: list[str] = []
    dependency_groups = dependencies_grouped_by_extra(pkg)
    installed = {distro.name for distro in importlib.metadata.distributions()}
    for extra in extras:
        try:
            dependencies = {*dependency_groups[extra]}
        except KeyError:
            raise ValueError(
                f"{extra=} couldn't be resolved from those collected: "
                f"{[k for k in dependency_groups if k]}."
            )
        if missing_extra := dependencies - installed:
            warnings.warn(
                f"\n    The feature you're trying to use requires the extra '{extra}', "
                f"\n    install it by running `pip install {pkg}[{extra}]`.",
                stacklevel=2,
            )
            missing.extend(missing_extra)
    if eager and missing:
        raise ImportError(f"Could not import uninstalled distributions: {missing}.")
