import logging
from pathlib import Path
from inex.inex import start
from inex.engine import execute
from typing import Optional, Union


def call_engine(
        config,
        log_level: Optional[str] = None,
        log_path: Optional[Union[str, Path]] = None,
        sys_path: Optional[str] = None,
        stop_after: Optional[str] = None,
):
    if isinstance(config, dict):
        state = {
            'command_line': None,
            'config_path': None,
        }
        return execute(config=config, state=state, stop_after=stop_after)
    else:
        return start(
            log_level=log_level,
            log_path=log_path,
            sys_path=sys_path,
            merge=None,
            update=None,
            config_path=str(config),
            stop_after=stop_after,
        )

def close_logger():
    logger = logging.getLogger('root')
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            logger.removeHandler(handler)
    logging.shutdown()
