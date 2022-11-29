
class Calculator:
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2

    def run(self):
        print(f'{self.value1} x {self.value2} = {self.value1 * self.value2}')
