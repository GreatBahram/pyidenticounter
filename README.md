# PyICounter

A simple tool for counting the number of identifiers inside a given python module.

## Installation 

```
pip install pyidenticounter
```

## Examples

```shell
pyicounter file1.py file2.py

# or you can run it on a directory and it will find all python files

pyicounter .
```

## Road-map

- [X] Discover python files from a given directory
- [X] Add test cases, run with pytest
- [X] Publish it to Github, using poetry
- [ ] Find variable names with annotations
- [ ] Run tests using Github Actions
