import os
import gzip
import glob
import shutil
import logging
import hashlib
import subprocess
from pathlib import Path
from omegaconf import OmegaConf
from typing import Optional, List, Dict, Union, Any
from inex.engine import execute as exec_inex
from inex.utils.configure import load_config, create_plugin, bind_plugins


def assign(value):
    return value


def read_text(path):
    path = Path(path)
    assert path.is_file(), f'File {path} does not exist'
    return path.read_text()


def evaluate(expression: str, initialize: List[str] = None, **kwargs):
    if initialize is not None:
        for sentence in initialize:
            exec(sentence)
    expression = expression.format(**kwargs)
    return eval(expression)


def attribute(modname, attname):
    logging.debug(f'Loading module {modname}')
    module = __import__(modname, fromlist=[''])
    assert hasattr(module, attname), f'Module {modname} does not have attribute {attname}'
    return getattr(module, attname)


_cache_ = dict()


def _import_(plugin, config, depends=None, ignore=None, **kwargs):
    path = os.path.abspath(config)
    assert os.path.isfile(path), f'File {path} does not exist'
    plugin = plugin.strip()
    assert len(plugin) > 0, 'Empty plugin or attribute name'
    parts = plugin.split('.')
    if len(parts) == 1:
        normal_name = plugin
        cache_name = 'plugins.' + plugin
    else:
        assert len(parts) == 2, f'Wrong plugin or attribute name: "{plugin}"'
        if parts[0] == 'plugins':
            normal_name = parts[1]
            cache_name = plugin
        else:
            normal_name = parts[0]
            cache_name = plugin
    if path in _cache_:
        logging.debug('Getting state dictionary from cache')
        state = _cache_[path]
    else:
        logging.debug('Creating new cache entry for state dictionary')
        state = dict()
        _cache_[path] = state
    if cache_name in state:
        return state[cache_name]
    logging.debug(f'Loading config from {path}')
    config = load_config(path)
    logging.debug(f'Merging config with options\n{kwargs}')
    config = OmegaConf.merge(config, kwargs)
    logging.debug(f'Resolving config\n{config}')
    config = OmegaConf.to_container(config, resolve=True, throw_on_missing=True)
    logging.debug(f'Building plugin dependencies in config\n{config}')
    bind_plugins(config)
    logging.debug(f'Final config:\n{config}')
    assert 'plugins' in config, f'Failed to find "plugins" list in config\n{config}'
    plugins = config['plugins']
    assert isinstance(plugins, list), f'Wrong type of "plugins" {type(plugins)} (must be list)'
    assert normal_name in plugins, f'Failed to find plugin "{normal_name}" in the list of plugins in config\n{config}'
    assert normal_name in config, f'Failed to find plugin "{normal_name}" in config\n{config}'
    options = config[normal_name]
    depends = {normal_name} if depends is None else set(depends) | {normal_name}
    if 'depends' in options:
        depends |= set(options['depends'])
    if ignore is not None:
        ignore = set(ignore)
    value = None
    for name in plugins:
        if name not in depends:
            continue
        elif (ignore is not None) and (name in ignore):
            continue
        cname = f'plugins.{name}'
        if cname in state:
            value = state[cname]
        else:
            create_plugin(name, config, state)
        if name == normal_name:
            assert cache_name in state, f'Failed to find created plugin {name} in the state dictionary'
            value = state[cache_name]
            break
    return value


def show(**kwargs):
    for key, value in kwargs.items():
        print(f'\n{key}\n  type: {type(value)}\n  id: {id(value)}\n  value: {value}')


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


def check_existence(pathnames):
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
        assert next(items, None) is not None, f'File or directory {pathname} ({recursive=}) does not exist'


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


def stage(
    config_path: str,
    merge_paths: Optional[Union[str, List[str]]] = None,
    override: Optional[Union[str, List[str], Dict[str, Any]]] = None,
    title: Optional[str] = None,
    must_exist: Optional[Union[str, List, Dict]] = None,
    check_md5: Optional[Union[str, List, Dict]] = None,
    cleanup: Optional[Union[str, List, Dict]] = None,
    make_dirs: Optional[Union[str, List]] = None,
    final_path: Optional[str] = None,
    done_mark: Optional[str] = None,
    disable: bool = False,
    force: bool = False,
) -> Any:
    if force:
        if title is not None:
            print(f'{title} - [ Forced ]')
    else:
        if disable:
            if title is not None:
                print(f'{title} - [ Disabled ]')
            return
        if done_mark is not None:
            done_mark = Path(done_mark)
            if done_mark.exists():
                if title is not None:
                    print(f'{title} - [ Done ]')
                return
        if title is not None:
            print(title)

    config_path = Path(config_path).absolute()
    assert config_path.is_file(), f'File {config_path} does not exist'

    if must_exist is not None:
        check_existence(must_exist)
    if check_md5 is not None:
        check_md5_hash(check_md5)
    if cleanup is not None:
        remove_paths(cleanup)
    if make_dirs is not None:
        make_directories(make_dirs)

    if done_mark is not None:
        done_mark = Path(done_mark).absolute()
        if not done_mark.parent.exists():
            logging.debug(f'Creating directory {done_mark.parent}')
            done_mark.parent.mkdir(parents=True, exist_ok=True)

    logging.debug('Reading configuration')
    config = load_config(config_path)
    if merge_paths is not None:
        if isinstance(merge_paths, str):
            merge_paths = [merge_paths]
        logging.debug(f'Merging configs {merge_paths}')
        configs = [config]
        for path in merge_paths:
            configs.append(load_config(path))
        config = OmegaConf.merge(*configs)
    if override is not None:
        if isinstance(override, str):
            override = [override]
        logging.debug(f'Overriding options:\n{override}')
        if isinstance(override, list):
            config = OmegaConf.merge(config, OmegaConf.from_dotlist(override))
        else:
            config = OmegaConf.merge(config, override)
    logging.debug(f'Resolving config\n{config}')
    config = OmegaConf.to_container(config, resolve=True, throw_on_missing=True)
    logging.debug(f'Building plugin dependencies in config\n{config}')
    bind_plugins(config)
    logging.debug(f'Final config:\n{OmegaConf.to_yaml(OmegaConf.create(config))}')

    if final_path is not None:
        final_path = Path(final_path)
        parent = final_path.parent
        if not parent.exists():
            logging.debug(f'Creating directory {parent}')
            parent.mkdir(parents=True, exist_ok=True)
        logging.debug(f'Writing final config to {final_path}')
        with final_path.open('wt', encoding='utf-8') as stream:
            print(OmegaConf.to_yaml(config), file=stream)

    logging.debug(f'Executing {config_path}')
    state = {'config_path': config_path}
    result = exec_inex(config=config, state=state)

    if done_mark is not None:
        logging.debug(f'Creating file {done_mark}')
        done_mark.touch(exist_ok=True)

    return result


def write_script(path: str, text: str):
    path = Path(path)
    if not path.parent.exists():
        logging.debug(f'Creating directory {path.parent}')
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def execute(
    executable: str,
    arguments: Optional[Union[str, List[str]]] = None,
    title: Optional[str] = None,
    must_exist: Optional[Union[str, List, Dict]] = None,
    check_md5: Optional[Union[str, List, Dict]] = None,
    cleanup: Optional[Union[str, List, Dict]] = None,
    make_dirs: Optional[Union[str, List]] = None,
    script_path: Optional[str] = None,
    script_text: Optional[str] = None,
    log_file: Optional[str] = None,
    done_mark: Optional[str] = None,
    disable: bool = False,
    force: bool = False,
    silent: bool = False,
) -> None:
    if force:
        if title is not None:
            print(f'{title} - [ Forced ]')
    else:
        if disable:
            if title is not None:
                print(f'{title} - [ Disabled ]')
            return
        if done_mark is not None:
            done_mark = Path(done_mark)
            if done_mark.exists():
                if title is not None:
                    print(f'{title} - [ Done ]')
                return
        if title is not None:
            print(title)

    if must_exist is not None:
        check_existence(must_exist)
    if check_md5 is not None:
        check_md5_hash(check_md5)
    if cleanup is not None:
        remove_paths(cleanup)
    if make_dirs is not None:
        make_directories(make_dirs)

    exec_path = shutil.which(executable)
    if exec_path is not None:
        executable = exec_path
    if arguments is None:
        arguments = list()
    elif isinstance(arguments, str):
        arguments = [arguments]
    else:
        arguments = [str(arg) for arg in arguments]
    command = [executable] + arguments

    if log_file is not None:
        log_file = Path(log_file).absolute()
        if not log_file.parent.exists():
            logging.debug(f'Creating directory {log_file.parent}')
            log_file.parent.mkdir(parents=True, exist_ok=True)

    if done_mark is not None:
        done_mark = Path(done_mark).absolute()
        if not done_mark.parent.exists():
            logging.debug(f'Creating directory {done_mark.parent}')
            done_mark.parent.mkdir(parents=True, exist_ok=True)

    if script_path is not None:
        logging.debug(f'Writing script {script_path}')
        write_script(script_path, script_text)

    logging.debug(f'Executing command:\n{command}')
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    with OptionalFile(log_file, mode='wt') as stream:
        while True:
            line = process.stdout.readline()
            if len(line) == 0:
                break
            line = line.decode(encoding='utf-8').rstrip()
            if not silent:
                print(line)
            if stream is not None:
                print(line, file=stream)
    process.communicate()
    assert process.returncode == 0, f'Failed to execute command\n"{command}"'

    if done_mark is not None:
        logging.debug(f'Creating file {done_mark}')
        done_mark.touch(exist_ok=True)


def system(
    command: str,
    title: Optional[str] = None,
    must_exist: Optional[Union[str, List, Dict]] = None,
    check_md5: Optional[Union[str, List, Dict]] = None,
    cleanup: Optional[Union[str, List, Dict]] = None,
    make_dirs: Optional[Union[str, List]] = None,
    script_path: Optional[str] = None,
    script_text: Optional[str] = None,
    done_mark: Optional[str] = None,
    disable: bool = False,
    force: bool = False,
) -> None:
    if force:
        if title is not None:
            print(f'{title} - [ Forced ]')
    else:
        if disable:
            if title is not None:
                print(f'{title} - [ Disabled ]')
            return
        if done_mark is not None:
            done_mark = Path(done_mark)
            if done_mark.exists():
                if title is not None:
                    print(f'{title} - [ Done ]')
                return
        if title is not None:
            print(title)

    if must_exist is not None:
        check_existence(must_exist)
    if check_md5 is not None:
        check_md5_hash(check_md5)
    if cleanup is not None:
        remove_paths(cleanup)
    if make_dirs is not None:
        make_directories(make_dirs)

    if done_mark is not None:
        done_mark = Path(done_mark).absolute()
        if not done_mark.parent.exists():
            logging.debug(f'Creating directory {done_mark.parent}')
            done_mark.parent.mkdir(parents=True, exist_ok=True)

    if script_path is not None:
        logging.debug(f'Writing script {script_path}')
        write_script(script_path, script_text)

    logging.debug(f'Executing command:\n{command}')
    code = subprocess.call(command, shell=True)
    assert code == 0, f'Failed to execute command\n"{command}"'

    if done_mark is not None:
        logging.debug(f'Creating file {done_mark}')
        done_mark.touch(exist_ok=True)
