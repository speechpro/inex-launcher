import gzip
import glob
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Optional, Mapping


def compute_md5_hash(path):
    path = Path(path)
    assert path.is_file(), f'File {path} does not exist'
    md5_hash = hashlib.md5()
    with path.open(mode='rb') as stream:
        for buffer in iter(lambda: stream.read(4096), b''):
            md5_hash.update(buffer)
    return md5_hash.hexdigest()


def check_md5_hash(pathnames):
    if isinstance(pathnames, dict):
        pathnames = [pathnames]
    for pathname in pathnames:
        path = Path(pathname['path'])
        assert path.is_file(), f'File {path} does not exist'
        md5_ref = pathname['md5']
        md5_hyp = compute_md5_hash(pathname['path'])
        assert md5_hyp == md5_ref, f'Wrong MD5 {md5_hyp} (must be {md5_ref}) for file {path}'


def check_existence(pathnames, plugin: Optional[str] = None):
    if isinstance(pathnames, str):
        pathnames = [{'pathname': pathnames, 'recursive': False}]
    elif isinstance(pathnames, dict):
        pathnames = [pathnames]
    elif isinstance(pathnames, list):
        items = list()
        for pathname in pathnames:
            if isinstance(pathname, str):
                items.append({'pathname': pathname, 'recursive': False})
            else:
                items.append(pathname)
        pathnames = items
    for pathname in pathnames:
        recursive = pathname['recursive']
        pathname = pathname['pathname']
        items = iter(glob.iglob(pathname, recursive=recursive))
        item = next(items, None)
        if plugin is None:
            assert item is not None, f'File or directory {pathname} ({recursive=}) does not exist'
        else:
            assert item is not None, f'File or directory {pathname} ({recursive=}) required by the {plugin} plugin does not exist'


def remove_paths(pathnames):
    if isinstance(pathnames, str):
        pathnames = [{'pathname': pathnames, 'recursive': False}]
    elif isinstance(pathnames, dict):
        pathnames = [pathnames]
    elif isinstance(pathnames, list):
        items = list()
        for pathname in pathnames:
            if isinstance(pathname, str):
                items.append({'pathname': pathname, 'recursive': False})
            else:
                items.append(pathname)
        pathnames = items
    for pathname in pathnames:
        for path in glob.iglob(pathname['pathname'], recursive=pathname['recursive']):
            path = Path(path)
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(str(path))


def make_directories(pathnames):
    if isinstance(pathnames, str):
        pathnames = [pathnames]
    for path in pathnames:
        path = Path(path)
        if not path.is_dir():
            logging.debug(f'Creating directory {path}')
            path.mkdir(parents=True, exist_ok=True)


def execute_commands(commands: Mapping[str, str], **kwargs):
    for command, arguments in commands.items():
        logging.debug(f'Executing {command} with arguments {arguments}')
        if command == 'exists':
            check_existence(arguments, **kwargs)
        elif command == 'delete':
            remove_paths(arguments)
        elif command == 'mkdir':
            make_directories(arguments)
        else:
            raise NameError(f'Unknown command: {command}')


class OptionalFile:
    def __init__(self, path=None, mode='rt', encoding='utf-8'):
        self.path = path
        self.mode = mode
        self.encoding = encoding
        self.file = None

    def __enter__(self):
        if self.path is None:
            self.file = None
        else:
            path = Path(self.path).absolute()
            if not path.parent.exists():
                logging.debug(f'Creating directory {path.parent}')
                path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == '.gz':
                self.file = gzip.open(str(path), mode=self.mode, encoding=self.encoding)
            else:
                self.file = path.open(mode=self.mode, encoding=self.encoding)
        return self.file

    def __exit__(self, type, value, traceback):
        if self.file is not None:
            self.file.close()
            self.file = None
