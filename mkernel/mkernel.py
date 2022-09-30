import re
import sys
import time
import datetime
import logging
import argparse
from mkernel.utils.options import Options
from mkernel.utils.configure import configure_logging, load_config
from mkernel.engine import Engine


def main():
    time_total = time.time()

    parser = argparse.ArgumentParser(description='Microkernel')
    parser.add_argument('--log-level', '-l', type=str, default='WARNING', help='Set the root logger level.')
    parser.add_argument('--log-path', '-g', type=str, help='Path to the log-file.')
    parser.add_argument('--sys-paths', '-s', type=str, help='Paths to add to the list of system paths (sys.path).')
    parser.add_argument('--override', '-o', type=str, action='append', help='Options to be overridden (in "dot" notation: "key1.key2=value").')
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
    config = Options(load_config(args.config_path))
    if args.override is not None:
        for option in args.override:
            parts = option.split('=')
            assert len(parts) == 2, f'Wrong value of the command line "--override" option "{option}" (must be in form "key1=value")'
            key, value = parts
            logging.info(f'Updating config: {key}: {config[key]} ==> {value}')
            config[key] = value
    config.resolve()
    logging.info(f'Config:\n{config.yaml()}')

    state = Options()
    state['command_line'] = ' '.join(sys.argv)
    logging.info(state['command_line'])
    state['config_path'] = args.config_path

    engine = Engine(config=config, state=state)
    engine.run()

    time_total = int(time.time() - time_total)
    time_total = f'{datetime.timedelta(seconds=time_total)} ({int(time_total)} sec)'
    logging.info(f'Total time: {time_total}')
    logging.info(f'Finished')


if __name__ == '__main__':
    main()
