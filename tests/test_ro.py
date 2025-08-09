import unittest
from asyncframework.util.ro import ReadOnly

class InternalToReadonly():
    d: int = 2
    e: str = "test"
    f = None


class ToBeReadonly():
    a: int = 0
    b: float = 10
    c: InternalToReadonly = InternalToReadonly()


class TestROClass(unittest.TestCase):
    def test_readonly(self):
        notreadonly = ToBeReadonly()
        readonlyclass: ToBeReadonly = ReadOnly.make_ro(notreadonly)
        with self.assertRaises(RuntimeError):
            readonlyclass.a = 10
        with self.assertRaises(RuntimeError):
            readonlyclass.c.d = 2
        self.assertEqual(readonlyclass.b, 10)
        with self.assertRaises(AttributeError):
            x = readonlyclass.c.g # type: ignore # Showcase for undefined members
        self.assertEqual(readonlyclass.c.d, 2)
        a:int = readonlyclass.a
        a = 5
        self.assertEqual(a, 5)
        self.assertEqual(readonlyclass.a, 0)
