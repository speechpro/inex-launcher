import re
import sys
import time
import datetime
import logging
import argparse
from omegaconf import OmegaConf
from inex.utils.configure import configure_logging, load_config
from inex.engine import Engine


'''

-l DEBUG tests/configs/message.yaml
-l DEBUG tests/configs/compute1.yaml
-l DEBUG tests/configs/compute2.yaml

-l DEBUG
 -m tests/configs/part2.yaml
 -m tests/configs/part3.yaml
 -m tests/configs/part4.yaml
 tests/configs/part1.yaml

-l DEBUG
 -u "generator1.options.a=100"
 -u "generator1.options.b=200"
 tests/configs/compute1.yaml

-l DEBUG
 -o "generator1.options.a=100"
 -o "generator1.options.b=200"
 tests/configs/compute1.yaml

'''


def main():
    time_total = time.time()

    parser = argparse.ArgumentParser(description='Microkernel')
    parser.add_argument('--log-level', '-l', type=str, default='WARNING', help='Set the root logger level.')
    parser.add_argument('--log-path', '-g', type=str, help='Path to the log-file.')
    parser.add_argument('--sys-paths', '-s', type=str, help='Paths to add to the list of system paths (sys.path).')
    parser.add_argument('--merge', '-m', type=str, action='append', help='Path to the configuration file to be merged with the main config.')
    parser.add_argument('--update', '-u', type=str, action='append', help='Option to be updated (in "dot" notation: "key1.key2=value").')
    parser.add_argument('--override', '-o', type=str, action='append', help='Deprecated! Same as --update. Kept for backward compatibility.')
    parser.add_argument('config_path', type=str, help='Path to the configuration file (in YAML or JSON) or string with configuration in YAML.')
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

    time_total = int(time.time() - time_total)
    time_total = f'{datetime.timedelta(seconds=time_total)} ({int(time_total)} sec)'
    logging.info(f'Total time: {time_total}')
    logging.info(f'Finished')


if __name__ == '__main__':
    main()
