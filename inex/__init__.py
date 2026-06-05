from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version('inex-launcher')
except PackageNotFoundError:
    __version__ = 'failed-to-get-version'
