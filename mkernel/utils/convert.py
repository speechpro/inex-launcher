

def str_to_bool(value):
    if isinstance(value, bool):
        return value
    assert isinstance(value, str), f'Wrong value type "{type(value)}" (must be str or bool)'
    if (
        (value == 'True')
        or (value == 'true')
        or (value == 'Yes')
        or (value == 'YES')
        or (value == 'yes')
        or (value == 'Y')
        or (value == 'y')
        or (value == '1')
    ):
        return True
    return False
