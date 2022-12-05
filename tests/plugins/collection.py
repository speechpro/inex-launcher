

class Number:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


class Runner:
    def __init__(self, number1, number2, number3, plugin1, plugin2, plugin3, arr_val1, dic_val1):
        self.number1 = number1
        self.number2 = number2
        self.number3 = number3
        self.plugin1 = plugin1
        self.plugin2 = plugin2
        self.plugin3 = plugin3
        self.arr_val1 = arr_val1
        self.dic_val1 = dic_val1

    def check(self, number1, number2, number3, number4, plugin1, plugin2, plugin3, arr_val2, dic_val2, arr_val3, dic_val3):
        assert number1 == self.number1
        assert number2 == self.number2
        assert number3 == self.number3
        assert number4 == 23
        assert plugin1() == self.number1
        assert self.plugin1() == self.number1
        assert plugin2() == self.number2
        assert self.plugin2() == self.number2
        assert plugin3() == self.number3
        assert self.plugin3() == self.number3
        assert len(arr_val2) == len(self.arr_val1)
        assert len(arr_val3) == len(self.arr_val1)
        assert len(dic_val2) == len(self.dic_val1)
        assert len(dic_val3) == len(self.arr_val1)
        for i in range(len(self.arr_val1)):
            assert arr_val2[i] == self.arr_val1[i]
            assert arr_val3[i] == self.arr_val1[i]
        for key, value in self.dic_val1.items():
            assert dic_val2[key] == value
            assert dic_val3[key] == value
