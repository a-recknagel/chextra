import importlib

import pytest


@pytest.mark.parametrize(
    "module",
    ["chextra"],
)
def test_import(module):
    importlib.import_module(module)
