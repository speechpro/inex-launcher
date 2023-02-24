

def show(**kwargs):
    for key, value in kwargs.items():
        print(f'\n{key}\n  type: {type(value)}\n  value: {value}')
