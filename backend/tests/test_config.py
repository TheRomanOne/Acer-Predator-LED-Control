import pytest
from pydantic import ValidationError

from led_studio.config import Settings


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_loopback_hosts_are_accepted(host: str) -> None:
    assert Settings(host=host).host == host


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.10", "::"])
def test_non_loopback_host_is_refused(host: str) -> None:
    # The API has no authentication, so exposing it beyond this machine is never safe.
    with pytest.raises(ValidationError, match="loopback"):
        Settings(host=host)
