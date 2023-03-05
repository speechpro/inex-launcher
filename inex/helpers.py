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


def evaluate(
        expression,
        a=None, b=None, c=None, d=None,
        x=None, y=None, z=None, w=None,
        i=None, j=None, k=None,
        m=None, n=None,
):
    return eval(expression)


def attribute(modname, attname):
    logging.debug(f'Loading module {modname}')
    module = __import__(modname, fromlist=[''])
    assert hasattr(module, attname), f'Module {modname} does not have attribute {attname}'
    return getattr(module, attname)


def posit_args(modname, attname, arguments):
    if isinstance(modname, str):
        logging.debug(f'Loading module {modname}')
        module = __import__(modname, fromlist=[''])
    else:
        module = modname
    assert hasattr(module, attname), f'Module {modname} does not have attribute {attname}'
    return getattr(module, attname)(*arguments)


def show(**kwargs):
    for key, value in kwargs.items():
        print(f'\n{key}\n  type: {type(value)}\n  value: {value}')
