import re
import sys
import logging
import argparse
from omegaconf import OmegaConf
from datetime import datetime, timedelta
from inex.utils.configure import configure_logging, load_config
from inex.engine import Engine


def main():
    begin_time = datetime.now()

    parser = argparse.ArgumentParser(description='InEx')
    parser.add_argument('--log-level', '-l', type=str, default='WARNING', help='set the root logger level')
    parser.add_argument('--log-path', '-g', type=str, help='path to the log-file')
    parser.add_argument('--sys-paths', '-s', type=str, help='paths to add to the list of system paths (sys.path)')
    parser.add_argument('--merge', '-m', type=str, action='append', help='path to the configuration file to be merged with the main config')
    parser.add_argument('--update', '-u', type=str, action='append', help='option to be updated (in "dot" notation: "key1.key2=value")')
    parser.add_argument('--override', '-o', type=str, action='append', help='deprecated, same as --update, kept for backward compatibility')
    parser.add_argument('config_path', type=str, help='path to the configuration file (in YAML or JSON) or string with configuration in YAML')
    args = parser.parse_args()

    configure_logging(log_level=args.log_level, log_path=args.log_path)

    if (args.sys_paths is not None) and (len(args.sys_paths) > 0):
        paths = re.split(r'[:;,|]', args.sys_paths)
        for path in paths:
            if path not in sys.path:
                logging.info(f'Adding {path} to sys.path')
                sys.path.append(path)

    logging.info('Reading configuration')
    config = load_config(args.config_path)
    if args.merge is not None:
        configs = [config]
        for path in args.merge:
            configs.append(load_config(path))
        config = OmegaConf.merge(*configs)
    dot_list = list()
    if args.update is not None:
        dot_list += args.update
    if args.override is not None:
        dot_list += args.override
    if len(dot_list) > 0:
        options = OmegaConf.from_dotlist(dot_list)
        config = OmegaConf.merge(config, options)
    config = OmegaConf.to_container(config, resolve=True, throw_on_missing=True)
    logging.info(f'Config:\n{OmegaConf.to_yaml(OmegaConf.create(config))}')

    state = dict()
    state['command_line'] = ' '.join(sys.argv)
    logging.info(state['command_line'])
    state['config_path'] = args.config_path

    logging.debug('Creating inex engine')
    engine = Engine(config=config, state=state)
    logging.debug('Starting inex execution')
    engine()

    end_time = datetime.now()
    duration = timedelta(seconds=round((end_time - begin_time).total_seconds()))
    logging.info(f'Started at {begin_time.date()} {begin_time.strftime("%H:%M:%S")}')
    logging.info(f'Finished at {end_time.date()} {end_time.strftime("%H:%M:%S")}')
    logging.info(f'Total time {duration} ({duration.total_seconds():.0f} sec)')


if __name__ == '__main__':
    main()
