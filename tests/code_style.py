"""RDT code style module."""

import importlib
import inspect
from pathlib import Path
from types import FunctionType

import pytest

from rdt.transformers import TRANSFORMERS, get_transformer_class
from rdt.transformers.base import BaseTransformer


def validate_transformer_subclass(transformer):
    """Test whether or not the ``Transformer`` is a subclass of ``BaseTransformer``."""
    fail_message = 'Transformer must be a subclass of ``BaseTransformer``.'
    assert issubclass(transformer, BaseTransformer), fail_message


def validate_transformer_module(transformer):
    """Test whether or not the ``Transformer`` is inside the right module."""
    transformer_file = Path(inspect.getfile(transformer))
    transformer_folder = transformer_file.parent
    is_valid = False

    if transformer_folder.match('transformers'):
        is_valid = True
    elif transformer_folder.parent.match('transformers'):
        is_valid = True

    assert is_valid, 'The transformer module is not placed inside a valid path.'


def validate_transformer_importable_from_parent_module(transformer):
    """Validate wheter the transformer can be imported from the parent module."""
    name = transformer.get_name()
    module = getattr(transformer, '__module__', '')
    module = module.rsplit('.', 1)[0]
    imported_transformer = getattr(importlib.import_module(module), name, None)
    assert imported_transformer is not None, f'Could not import {name} from {module}'


def get_test_location(transformer):
    """Return the expected unit test location of a transformer."""
    transformer_file = Path(inspect.getfile(transformer))
    transformer_folder = transformer_file.parent
    rdt_unit_test_path = Path(__file__).parent / 'unit'

    test_location = None
    if transformer_folder.match('transformers'):
        test_location = rdt_unit_test_path / 'transformers' / f'test_{transformer_file.name}'

    elif transformer_folder.parent.match('transformers'):
        test_location = rdt_unit_test_path / 'transformers' / transformer_folder.name
        test_location = test_location / f'test_{transformer_file.name}'

    return test_location


def validate_test_location(transformer):
    """Validate if the test file exists in the expected location."""
    test_location = get_test_location(transformer)
    if test_location is None:
        return False, 'The expected test location was not found.'

    assert test_location.exists(), 'The expected test location does not exist.'


def _load_module_from_path(path):
    """Return the module from a given ``PosixPath``."""
    assert path.exists(), 'The expected test module was not found.'
    module_path = path.parent
    module_name = path.name.split('.')[0]
    if module_path.name == 'transformers':
        module_path = f'rdt.transformers.{module_name}'
    elif module_path.parent.name == 'transformers':
        module_path = f'rdt.transformers.{module_path.parent.name}.{module_name}'

    spec = importlib.util.spec_from_file_location(module_path, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def validate_test_names(transformer):
    """Validate if the test methods are properly specified."""
    test_file = get_test_location(transformer)
    module = _load_module_from_path(test_file)

    test_class = getattr(module, f'Test{transformer.get_name()}', None)
    assert test_class is not None, 'The expected test class was not found.'

    test_functions = inspect.getmembers(test_class, predicate=inspect.isfunction)
    test_functions = [test for test, _ in test_functions if test.startswith('test')]

    assert test_functions, 'No test functions found within the test module.'

    transformer_functions = [
        name
        for name, function in transformer.__dict__.items()
        if isinstance(function, (FunctionType, classmethod, staticmethod))
    ]

    valid_test_functions = []
    for test in test_functions:
        count = len(valid_test_functions)
        for transformer_function in transformer_functions:
            simple_test = rf'test_{transformer_function}'
            described_test = rf'test_{transformer_function}_'
            if test.startswith(described_test):
                valid_test_functions.append(test)
            elif test.startswith(simple_test):
                valid_test_functions.append(test)

        fail_message = f'No function name was found for the test: {test}'
        assert len(valid_test_functions) > count, fail_message


@pytest.mark.parametrize('transformer', TRANSFORMERS.values(), ids=TRANSFORMERS.keys())  # noqa
def test_transformer_code_style(transformer):
    """Validate a transformer."""
    if not inspect.isclass(transformer):
        transformer = get_transformer_class(transformer)

    validate_transformer_subclass(transformer)
    validate_transformer_module(transformer)
    validate_test_location(transformer)
    validate_test_names(transformer)
    validate_transformer_importable_from_parent_module(transformer)
