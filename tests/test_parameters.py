import unittest

from modularfx.node.parameters import ParameterBase, ParameterStore, Parameter


class ParametersObject(ParameterBase):
    """Mock object to install parameters into"""
    _f = lambda: None

    def __call__(self):
        return self._f(**self.parameters.args())


class ParametersObjectEx(ParametersObject):
    """Mock object that extends ParametersObject"""
    pass


class TestBase(unittest.TestCase):
    """Test directly extending the base type"""
    base_type = ParametersObject

    def setUp(self):
        class AddClass(self.base_type):
            class Parameters(ParameterStore):
                a = Parameter(2, int)
                b = Parameter(3.0, float)

            def __call__(self):
                return self.parameters.a.value + self.parameters.b.value

        self.parameters_class = AddClass

    def test_types(self):
        assert(issubclass(self.parameters_class, self.base_type))
        self.assertIsInstance(self.parameters_class(), self.parameters_class)

    def test_defaults(self):
        x = self.parameters_class()
        self.assertEqual(x.parameters.a.default, 2)
        self.assertEqual(x.parameters.b.default, 3)
        self.assertEqual(x.parameters.a.type, int)
        self.assertEqual(x.parameters.b.type, float)
        self.assertEqual(x.parameters.a.name, 'a')
        self.assertEqual(x.parameters.b.name, 'b')

    def test_len(self):
        x = self.parameters_class()
        self.assertEqual(len(x.parameters), 2)

    def test_indexing(self):
        x = self.parameters_class()
        self.assertEqual(x.parameters[0].name, 'a')

    def test_values(self):
        x = self.parameters_class()
        self.assertEqual(x.parameters.a.value, 2)
        self.assertEqual(x.parameters.b.value, 3.0)
        
    def test_uniqueness(self):
        x = self.parameters_class()
        y = self.parameters_class()
        x.parameters.a.set(5)
        y.parameters.a.set(12)
        self.assertEqual(x.parameters.a.value, 5)
        self.assertEqual(y.parameters.a.value, 12)

    def test_serialization_none(self):
        x = self.parameters_class()
        s = x.parameters.serialize()
        self.assertEqual(len(s), 0) # no parameters have been set

    def test_serialization_default(self):
        x = self.parameters_class()
        x.parameters.a.set(x.parameters.a.default) # note, this is the default value
        s = x.parameters.serialize()
        self.assertIn('a', s)
        self.assertEqual(s['a'], x.parameters.a.default)

    def test_serialization_other(self):
        x = self.parameters_class()
        x.parameters.a.set(206)
        s = x.parameters.serialize()
        self.assertIn('a', s)
        self.assertEqual(s['a'], 206)

    def test_deserialize(self):
        x = self.parameters_class()
        x.parameters.a.set(206)
        s = x.parameters.serialize()
        y = self.parameters_class()
        y.parameters.deserialize(s)
        self.assertEqual(y.parameters.a.value, 206)

    def test_usage(self):
        x = self.parameters_class()
        self.assertEqual(x(), 5)


class TestFunctionDecorator(TestBase):
    """Test wrapping a class in a ParametersObject"""
    def setUp(self):
        @ParameterStore.install(self.base_type)
        def Add(a: int = 2, b: float = 3.0):
            return a + b
        self.parameters_class = Add


class TestWrappedClass(TestBase):
    "Test wrapping a class (rather than a function)"
    def setUp(self):
        class Thing:
            def __init__(self, a: int = 2, b: float = 3.0):
                self.a = a
                self.b = b

        WrappedThing = ParameterStore.install(self.base_type)(Thing)
        self.parameters_class = WrappedThing
        self.parameters_instance = WrappedThing()
        self.result_type = Thing

    def test_usage(self):
        x = self.parameters_class()
        thing = x()
        self.assertIsInstance(thing, self.result_type)
        self.assertEqual(thing.a, 2)
        self.assertEqual(thing.b, 3.0)


class TestWrappedClassDecorator(TestWrappedClass):
    "Test wrapping a class (rather than a function)"
    def setUp(self):
        class Thing:
            def __init__(self, a: int = 2, b: float = 3.0):
                self.a = a
                self.b = b

        @ParameterStore.install(self.base_type)
        class WrappedThing(Thing):
            pass

        # note: we could wrap thing directly, but then we wouldn't
        # have access to the internal class for testing
        self.parameters_class = WrappedThing
        self.parameters_instance = WrappedThing()
        self.result_type = Thing


class TestExtend(TestBase):
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


class TestExtendWrapped(TestBase):
    """Test extending a wrapped object"""
    def setUp(self):
        @ParameterStore.install(self.base_type)
        def Add(a: int = 2, b: float = 3.0):
            return a + b

        class AddEx(Add):
            class Parameters(Add.Parameters):
                c = Parameter('hello', str)

            def __call__(self):
                return self._f(self.parameters.a.value, self.parameters.b.value)

        self.parameters_class = AddEx
        self.parameters_instance = self.parameters_class()

    def test_c(self):
        self.assertEqual(self.parameters_instance.parameters.c.default, 'hello')

    def test_len(self):
        x = self.parameters_class()
        self.assertEqual(len(x.parameters), 3)


# now repeat all tests, but with a subclass of ParametersObject

class TestBaseEx(TestBase):
    base_type = ParametersObjectEx

class TestFunctionDecoratorEx(TestFunctionDecorator):
    base_type = ParametersObjectEx

class TestWrappedClassEx(TestWrappedClass):
    base_type = ParametersObjectEx

class TestWrappedClassDecoratorEx(TestWrappedClassDecorator):
    base_type = ParametersObjectEx

class TestExtendEx(TestExtend):
    base_type = ParametersObjectEx

class TestExtendWrappedEx(TestExtendWrapped):
    base_type = ParametersObjectEx
