"""pytest_resources.errors: the typed failure surface of the resources plugin."""


class ResourceError(Exception):
    """Base for every resources-plugin failure."""


class EntryNotFoundError(ResourceError, AttributeError):
    """A node was asked for an entry the indexed tree does not hold.

    Subclasses ``AttributeError`` so attribute access keeps its protocol while the
    error stays typed and catchable as ``ResourceError``.
    """
