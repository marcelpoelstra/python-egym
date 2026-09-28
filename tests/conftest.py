import pytest
import responses

import egym
from fakes import BASE_URL, EMAIL, PASSWORD, add_login


@pytest.fixture
def mocked():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def api(mocked):
    add_login(mocked)
    return egym.Api(EMAIL, PASSWORD, base_url=BASE_URL)
