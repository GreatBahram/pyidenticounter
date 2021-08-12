

# PyICounter

A simple tool for counting the number of identifiers (a.k.a vocabulary) inside a given python module(s).

It can extract function or method name, classes, and variables.

## Installation 

```
pip install pyidenticounter
```

## Usage

```python
# example.py
myvar1 = 12
myvar2: str = ''


def func1(*args):
    age = 10
    return None


def func2():
    def func3():
        pass
    pass


class Person:
    def get_full_name(self):
        pass
    class Meta:
        model = Person
```

* You can simply run the program by passing a couple python files or a directory to `pyicounter` and it'll find all `*.py` and `*.pyi` files for you.

```shell
$ pyicounter example.py
example.py: 11 # it shows we defined 10 vocabulary inside this module

$ pyicounter example.py -v # there are three verbosity mode
example.py:variable: 4
example.py:func_or_method: 4
example.py:arg: 1
example.py:class: 2

$ pyicounter example.py -vv # gives the most detailed report
example.py:1: variable 'myvar1'
example.py:2: variable 'myvar2'
example.py:5: func_or_method 'func1'
example.py:5: arg 'args'
example.py:6: variable 'age'
example.py:10: func_or_method 'func2'
example.py:11: func_or_method 'func3'
example.py:16: class 'Person'
example.py:17: func_or_method 'get_full_name'
example.py:19: class 'Meta'
example.py:20: variable 'model'
```

## Road-map

- [X] Discover python files from a given directory
- [X] Add test cases, run with pytest
- [X] Publish it to PyPi, using poetry
- [X] Find variable names with annotations
- [X] Run tests using Github Actions
- [x] Update the readme file to show use cases and feature
- [X] Add a feature to extract argument names of classes, functions and for loops.
- [X] Provide exclude option
