from textwrap import dedent

from pyidenticounter import IdentifierType, PyIdentifierCounter


def test_variable_names():
    code = dedent(
        """\
        city = 'Tokyo'

        def greeting(name):
            print('Hello', name)

        def second_greeting():
            age = 10
            name = 'Jack'
            text = greeting(name)
            print(text + str(age))
    """
    )
    checker = PyIdentifierCounter()
    identifiers = checker.check(code)
    expected = ["city", "age", "name", "text"]
    actual = [
        report.name for report in identifiers if report.type == IdentifierType.VAR
    ]
    assert actual == expected


def test_func_method_names():
    code = dedent(
        """\
        city = 'Tokyo'

        def func1():
            def func2():
                pass
            def func3():
                pass
            pass

        class MyClass:
            def new(self):
                pass

            class InnerClass:
                def method2():
                    pass
    """
    )
    checker = PyIdentifierCounter()
    identifiers = checker.check(code)
    expected = ["func1", "func2", "func3", "new", "method2"]
    actual = [
        report.name for report in identifiers if report.type == IdentifierType.FUNC
    ]
    assert actual == expected


def test_func_class_names():
    code = dedent(
        """\
        class Person:
            def __init__(self, name):
                self.name = name


        class UserModel:
            class Meta:
                model = Person
                fields = ('id', 'name')


        # dynamic class creation: we cannot detect this one
        DynamicClass = type("NewClassName", (), {})
        """
    )
    checker = PyIdentifierCounter()
    identifiers = checker.check(code)
    expected = ["Person", "UserModel", "Meta"]
    actual = [
        report.name for report in identifiers if report.type == IdentifierType.CLASS
    ]
    assert actual == expected


def test_func_variable_with_annotations():
    code = dedent(
        """\
        class Person:
            age: int
            age_with_default: int = 18


        name: str
        name_with_value: str = 'Micheal'
        """
    )
    checker = PyIdentifierCounter()
    identifiers = checker.check(code)
    expected = ["age", "age_with_default", "name", "name_with_value"]
    actual = [
        report.name for report in identifiers if report.type == IdentifierType.VAR
    ]
    assert actual == expected


def test_func_or_method_args():
    code = dedent(
        """\
        class Person:
            def upper(self, name):
                return name.upper()


        def add(item_a: int, item_b: int):
            return item_a + item_b


        def advanced_add(*numbers):
            return sum(numbers)


        def func3(*args, **kwargs):
          pass
        """
    )
    checker = PyIdentifierCounter()
    identifiers = checker.check(code)
    expected = ["name", "item_a", "item_b", "numbers", "args", "kwargs"]
    actual = [
        report.name for report in identifiers if report.type == IdentifierType.ARG
    ]
    assert actual == expected
