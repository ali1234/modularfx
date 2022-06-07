import unittest


from modularfx.node.node import Node
from modularfx.node.attributes import *


class TestDefined(unittest.TestCase):

    def setUp(self):
        class DefinedNode(Node):
            a = Parameter(default=2, annotation=int)
            b = Parameter(default=3, annotation=int)

            result = Output()

            @result.evaluator
            def result(self):
                return self.a.eval() + self.b.eval()

            @result.codegen
            def result(self):
                return f'{self.a.code()} + {self.b.code()}'

        self.node = DefinedNode()

    def test_annotation(self):
        self.assertEqual(self.node.a.annotation, int)
        self.assertEqual(self.node.b.annotation, int)

    def test_set(self):
        self.node.a.value = 4
        self.node.b.value = 5
        self.assertEqual(self.node._parameters, {'a': 4, 'b':5})
        self.assertEqual(self.node.a.default, 2)
        self.assertEqual(self.node.b.default, 3)
        self.assertEqual(self.node.a.value, 4)
        self.assertEqual(self.node.b.value, 5)
        self.assertEqual(self.node.result.eval(), 9)

    def test_default(self):
        self.assertFalse(self.node.a.is_set)
        self.assertFalse(self.node.b.is_set)
        self.assertNotIn('a', self.node._parameters)
        self.assertNotIn('b', self.node._parameters)
        self.assertEqual(self.node.a.value, self.node.a.default)
        self.assertEqual(self.node.b.value, self.node.b.default)
        self.assertEqual(self.node.a.value, 2)
        self.assertEqual(self.node.b.value, 3)

    def test_eval(self):
        self.assertEqual(self.node.result.eval(), 5)

    def test_code(self):
        self.assertEqual(self.node.result.code(), '2 + 3')

    def test_code_set(self):
        self.node.a.value = 4
        self.node.b.value = 5
        self.assertEqual(self.node.result.code(), '4 + 5')


class TestIntrospected(TestDefined):

    def setUp(self):
        @Node.introspect('result')
        def Add(a: int = 2, b: int = 3):
            return a + b

        self.node = Add()

    def test_code(self):
        self.assertEqual(self.node.result.code(), 'tests.test_node.Add(a=2, b=3)')

    def test_code_set(self):
        self.node.a.value = 4
        self.node.b.value = 5
        self.assertEqual(self.node.result.code(), 'tests.test_node.Add(a=4, b=5)')
