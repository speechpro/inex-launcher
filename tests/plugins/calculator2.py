
class Calculator:
    def __init__(self, generator, num_iters):
        self.generator = generator
        self.num_iters = num_iters

    def run(self):
        for i in range(self.num_iters):
            value1 = self.generator()
            value2 = self.generator()
            print(f'{i + 1}.  {value1} x {value2} = {value1 * value2}')
