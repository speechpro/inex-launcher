import re
import sys
import logging
import argparse
from pathlib import Path
from omegaconf import OmegaConf
from datetime import datetime, timedelta
from inex.utils.configure import configure_logging, load_config, bind_plugins
from inex.version import __version__
from inex.engine import execute


def fetch(path, value=None):
    path = Path(path)
    assert path.is_file(), f'File {path} does not exist'
    config = OmegaConf.load(path)
    if value is not None:
        config = eval(f'config.{value}')
    return config


def start(log_level, log_path, sys_paths, merge, update, config_path, stop_after=None, final_path=None):
    begin_time = datetime.now()

    OmegaConf.register_new_resolver('__fetch__', fetch, replace=True)

    configure_logging(log_level=log_level, log_path=log_path)

    if (sys_paths is not None) and (len(sys_paths) > 0):
        paths = re.split(r'[:;,|]', sys_paths)
        for path in paths:
            if path not in sys.path:
                logging.debug(f'Adding {path} to sys.path')
                sys.path.append(path)

    logging.debug('Reading configuration')
    config = load_config(config_path)
    if merge is not None:
        logging.debug(f'Merging configs {merge}')
        configs = [config]
        for path in merge:
            configs.append(load_config(path))
        config = OmegaConf.merge(*configs)
    dot_list = list()
    if update is not None:
        dot_list += update
    if len(dot_list) > 0:
        logging.debug(f'Applying updates {dot_list}')
        options = OmegaConf.from_dotlist(dot_list)
        config = OmegaConf.merge(config, options)
    logging.debug(f'Resolving config\n{config}')
    config = OmegaConf.to_container(config, resolve=True, throw_on_missing=True)
    logging.debug(f'Building plugin dependencies in config\n{config}')
    bind_plugins(config)
    logging.debug(f'Final config:\n{OmegaConf.to_yaml(OmegaConf.create(config))}')

    if final_path is not None:
        logging.debug(f'Writing final config to {final_path}')
        final_path = Path(final_path)
        parent = final_path.parent
        if not parent.exists():
            logging.debug(f'Creating directory {parent}')
            parent.mkdir(parents=True, exist_ok=True)
        with final_path.open('wt', encoding='utf-8') as stream:
            print(OmegaConf.to_yaml(config), file=stream)

    state = dict()
    state['command_line'] = ' '.join(sys.argv)
    logging.debug(state['command_line'])
    state['config_path'] = config_path

    logging.debug('Starting InEx execution')
    result = execute(config=config, state=state, stop_after=stop_after)

    end_time = datetime.now()
    duration = timedelta(seconds=round((end_time - begin_time).total_seconds()))
    print(f'\n# Started at {begin_time.date()} {begin_time.strftime("%H:%M:%S")}', file=sys.stderr)
    print(f'# Finished at {end_time.date()} {end_time.strftime("%H:%M:%S")}', file=sys.stderr)
    print(f'# Total time {duration} ({duration.total_seconds():.0f} sec)', file=sys.stderr)

    return result


def main():
    parser = argparse.ArgumentParser(description='InEx: Initialize & Execute')
    parser.add_argument('--version', '-v', action='version', version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument('--log-level', '-l', type=str, default='WARNING', help='set the root logger level')
    parser.add_argument('--log-path', '-g', type=str, help='path to the log-file')
    parser.add_argument('--sys-paths', '-s', type=str, help='paths to add to the list of system paths (sys.path)')
    parser.add_argument(
        '--merge', '-m',
        type=str,
        action='append',
        help='path to the configuration file to be merged with the main config'
    )
    parser.add_argument(
        '--update', '-u',
        type=str,
        action='append',
        help='update or set value for some parameter (use "dot" notation: "key1.key2=value")')
    parser.add_argument('--stop-after', '-a', type=str, help='stop execution after the specified plugin is initialized')
    parser.add_argument('--final-path', '-f', type=str, help='write final config to the specified file')
    parser.add_argument(
        'config_path',
        type=str,
        help='path to the configuration file (in YAML or JSON) or string with configuration in YAML'
    )
    args = parser.parse_args()
    start(
        log_level=args.log_level,
        log_path=args.log_path,
        sys_paths=args.sys_paths,
        merge=args.merge,
        update=args.update,
        config_path=args.config_path,
        stop_after=args.stop_after,
        final_path=args.final_path,
    )


if __name__ == '__main__':
    main()
