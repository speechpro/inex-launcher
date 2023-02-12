import unittest
from inex.utils.convert import str_to_bool


class UtilsConvertStrToBool(unittest.TestCase):
    def test_str_to_bool(self):
        self.assertTrue(str_to_bool('True'))
        self.assertTrue(str_to_bool('true'))
        self.assertTrue(str_to_bool('Yes'))
        self.assertTrue(str_to_bool('YES'))
        self.assertTrue(str_to_bool('yes'))
        self.assertTrue(str_to_bool('Y'))
        self.assertTrue(str_to_bool('y'))
        self.assertTrue(str_to_bool('1'))
        self.assertFalse(str_to_bool('False'))
        self.assertFalse(str_to_bool('false'))
        self.assertFalse(str_to_bool('No'))
        self.assertFalse(str_to_bool('NO'))
        self.assertFalse(str_to_bool('no'))
        self.assertFalse(str_to_bool('N'))
        self.assertFalse(str_to_bool('n'))
        self.assertFalse(str_to_bool('0'))
        self.assertTrue(str_to_bool(True))
        self.assertFalse(str_to_bool(False))


if __name__ == '__main__':
    unittest.main()
