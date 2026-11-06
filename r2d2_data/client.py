"""Python interface to the installed R2D2 client."""

from .common import drop_none


def _backend():
    try:
        import r2d2
    except ImportError as exc:
        raise RuntimeError(
            "The R2D2 client is not installed. Install it through your NASA/NCCS "
            "software environment before using this package."
        ) from exc
    return r2d2


class R2D2Client:
    """Thin, testable wrapper around the site-provided :mod:`r2d2` client."""

    def __init__(self, backend=None):
        self.backend = backend or _backend()

    def search(self, **kwargs):
        return self.backend.search(**drop_none(**kwargs))

    def fetch(self, **kwargs):
        return self.backend.fetch(**drop_none(**kwargs))


def search(**kwargs):
    return R2D2Client().search(**kwargs)


def fetch(**kwargs):
    return R2D2Client().fetch(**kwargs)
