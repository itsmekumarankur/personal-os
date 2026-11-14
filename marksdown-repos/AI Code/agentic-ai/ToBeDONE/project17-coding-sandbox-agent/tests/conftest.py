import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from attacks import cleanup, make_ctx  # noqa: E402
from sandbox import Limits, LocalProcessSandbox, NamespaceSandbox  # noqa: E402

needs_ns = pytest.mark.skipif(not NamespaceSandbox.available(), reason="needs Linux namespaces and root")
LIM = Limits(wall_s=4, cpu_s=2)


@pytest.fixture(scope="session")
def ctx():
    c = make_ctx()
    yield c
    cleanup(c)


@pytest.fixture
def l0():
    return LocalProcessSandbox(LIM)


@pytest.fixture
def l1():
    return NamespaceSandbox(LIM)
