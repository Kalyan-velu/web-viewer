# pip install pytest-mock pytest-asyncio

import pytest
from unittest.mock import patch, mock_open
from main import get_proxies


@pytest.mark.asyncio
async def test_get_proxies():
    m = mock_open(read_data="proxy1\nproxy2")
    with patch("builtins.open", m):
        proxies = await get_proxies('proxies.txt', print)
        assert proxies == ["134.73.98.130:6709:edrhvvie:qp58fbnkfhv6"
,"66.78.34.94:5713:edrhvvie:qp58fbnkfhv6"]


@pytest.mark.asyncio
async def test_get_proxies_exception():
    with patch("builtins.open", mock_open(read_data="proxy1\nproxy2")) as m:
        m.side_effect = IOError()
        proxies = await get_proxies('proxies.txt', print)
        assert proxies == []
