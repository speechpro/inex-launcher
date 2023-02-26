

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


def show(**kwargs):
    for key, value in kwargs.items():
        print(f'\n{key}\n  type: {type(value)}\n  value: {value}')
