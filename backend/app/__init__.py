"""GEO backend package."""

__all__ = ["app", "create_app"]


def __getattr__(name: str):
    if name in __all__:
        from app.main import app, create_app
        return app if name == "app" else create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
