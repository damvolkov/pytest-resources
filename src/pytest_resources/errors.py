"""pytest_resources.errors: the typed failure surface of the resources plugin."""


class ResourceError(Exception):
    """Base for every resources-plugin failure."""


class EntryNotFoundError(ResourceError, AttributeError):
    """A node was asked for an entry the indexed tree does not hold.

    Subclasses ``AttributeError`` so attribute access keeps its protocol while the
    error stays typed and catchable as ``ResourceError``.
    """


class ExtraNotInstalledError(ResourceError, ImportError):
    """A synthesis method was called without the optional extra that backs it.

    Subclasses ``ImportError`` so a missing dependency reads as what it is while
    staying catchable as ``ResourceError``; the message names the exact extra and
    the command that installs it.
    """
