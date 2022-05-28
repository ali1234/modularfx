import unittest

from modularfx.parameters import ParametersObject, ParameterStore, Parameter



class TestImpl:
    """Common tests"""
    base_type = ParametersObject

    def test_types(self):
        assert(issubclass(self.parameters_class, self.base_type))
        self.assertIsInstance(self.parameters_instance, self.parameters_class)

    def test_defaults(self):
        self.assertEqual(self.parameters_instance.parameters.a.default, 2)
        self.assertEqual(self.parameters_instance.parameters.b.default, 3)
        self.assertEqual(self.parameters_instance.parameters.a.type, int)
        self.assertEqual(self.parameters_instance.parameters.b.type, float)
        self.assertEqual(self.parameters_instance.parameters.a.name, 'a')
        self.assertEqual(self.parameters_instance.parameters.b.name, 'b')

    def test_values(self):
        self.assertEqual(self.parameters_instance.parameters.a.value, 2)
        self.assertEqual(self.parameters_instance.parameters.b.value, 3.0)
        
    def test_uniqueness(self):
        x = self.parameters_class()
        y = self.parameters_class()
        x.parameters.a.set(5)
        y.parameters.a.set(12)
        self.assertEqual(x.parameters.a.value, 5)
        self.assertEqual(y.parameters.a.value, 12)


class TestFunctionDecorator(TestImpl, unittest.TestCase):
    """Test wrapping a function in a ParametersObject"""

    def setUp(self):
        @ParameterStore.install(self.base_type)
        def Add(a: int = 2, b: float = 3.0):
            return a + b
        self.parameters_class = Add
        self.parameters_instance = Add()


class TestClass(TestImpl, unittest.TestCase):
    """Test wrapping a class in a ParametersObject"""
    def setUp(self):
        class Thing:
            def __init__(self, a: int = 2, b: float = 3.0):
                self.a = a
                self.b = b

        WrappedThing = ParameterStore.install(self.base_type)(Thing)
        self.parameters_class = WrappedThing
        self.parameters_instance = WrappedThing()
        self.result_type = Thing

    def test_result_type(self):
        thing = self.parameters_instance()
        self.assertIsInstance(thing, self.result_type)
        self.assertEqual(thing.a, 2)
        self.assertEqual(thing.b, 3.0)


class TestDeclare(TestImpl, unittest.TestCase):
    """Test declaring a ParametersObject directly, without wrapping anything"""
    def setUp(self):
        class AddClass(self.base_type):
            class Parameters(ParameterStore):
                a = Parameter(2, int)
                b = Parameter(3.0, float)

            def __call__(self):
                return self.parameters.a.value + self.parameters.b.value

        self.parameters_class = AddClass
        self.parameters_instance = self.parameters_class()


# wrapping/extending subclasses of ParametersObject should also work

class ParametersObjectEx(ParametersObject):
    pass

class TestFunctionDecoratorEx(TestFunctionDecorator):
    base_type = ParametersObjectEx


class TestClassEx(TestClass):
    base_type = ParametersObjectEx


class TestDeclareEx(TestDeclare):
    base_type = ParametersObjectEx


# wrapped objects should be able to be extended:

class TestExtend(TestDeclare):
    """Test extending an existing class"""
    def setUp(self):
        class AddBase(self.base_type):
            class Parameters(ParameterStore):
                a = Parameter(2, int)

        class AddEx(AddBase):
            class Parameters(AddBase.Parameters):
                b = Parameter(3.0, float)

            def __call__(self):
                return self.parameters.a.value + self.parameters.b.value

        self.parameters_class = AddEx
        self.parameters_instance = self.parameters_class()


class TestExtendWrapped(TestDeclare):
    def setUp(self):
        @ParameterStore.install(self.base_type)
        def Add(a: int = 2, b: float = 3.0):
            return a + b

        class AddEx(Add):
            class Parameters(Add.Parameters):
                c = Parameter('hello', str)

        self.parameters_class = AddEx
        self.parameters_instance = self.parameters_class()

    def test_c(self):
        self.assertEqual(self.parameters_instance.parameters.c.default, 'hello')
