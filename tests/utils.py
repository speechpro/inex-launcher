from inex.inex import start
from inex.engine import execute


def call_engine(config, stop_after=None):
    if isinstance(config, dict):
        state = {
            'command_line': None,
            'config_path': None,
        }
        return execute(config=config, state=state, stop_after=stop_after)
    else:
        return start(
            log_level='ERROR',
            log_path=None,
            sys_paths=None,
            merge=None,
            update=None,
            config_path=str(config),
            stop_after=stop_after,
        )
