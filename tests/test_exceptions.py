from egym.exceptions import ApiError, AuthenticationError, DiscoveryError, EgymError


def test_all_errors_share_the_base_class():
    assert all(issubclass(error, EgymError) for error in (ApiError, AuthenticationError, DiscoveryError))


def test_api_error_carries_response_details():
    error = ApiError(500, "https://example.com/np/thing", "boom")
    assert (error.status_code, error.url, error.text) == (500, "https://example.com/np/thing", "boom")
    assert "500" in str(error)


def test_authentication_error_carries_status():
    assert AuthenticationError("refused", 401).status_code == 401
    assert AuthenticationError("refused").status_code is None
