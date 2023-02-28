import logging


def none():
    return None


def zero():
    return 0


def one():
    return 1


def true():
    return True


def false():
    return False


def assign(value):
    return value


def attribute(modname, attname):
    logging.debug(f'Loading module {modname}')
    module = __import__(modname, fromlist=[''])
    assert hasattr(module, attname), f'Module {modname} does not have class {attname}'
    return getattr(module, attname)


def posit_args(modname, attname, arguments):
    logging.debug(f'Loading module {modname}')
    module = __import__(modname, fromlist=[''])
    assert hasattr(module, attname), f'Module {modname} does not have class {attname}'
    return getattr(module, attname)(*arguments)


def show(**kwargs):
    for key, value in kwargs.items():
        print(f'\n{key}\n  type: {type(value)}\n  value: {value}')
