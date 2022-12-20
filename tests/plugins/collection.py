

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


class TestResolve:
    def __init__(self, data1, data2):
        self.data1 = data1
        self.data2 = data2

    def test(self, data1, data2):
        for data in [data1, self.data1]:
            assert isinstance(data, list)
            assert len(data) == 3
            assert isinstance(data[0], int)
            assert data[0] == 1
            assert isinstance(data[1], list)
            assert len(data[1]) == 3
            assert data[1][0] == 1
            assert data[1][1] == 2
            assert data[1][2] == 3
            assert isinstance(data[2], dict)
            assert len(data[2]) == 3
            for i in range(1, 4):
                assert isinstance(data[2][i], Number)
                assert data[2][i].value == i

        for data in [data2, self.data2]:
            assert isinstance(data, dict)
            assert len(data) == 3
            assert isinstance(data[1], Number)
            assert isinstance(data[2], list)
            assert isinstance(data[3], dict)
            assert len(data[2]) == 3
            assert len(data[3]) == 3
            for i in range(3):
                assert isinstance(data[2][i], int)
                assert data[2][i] == i + 1
            for i in range(1, 4):
                assert isinstance(data[3][i], Number)
                assert data[3][i].value == i
