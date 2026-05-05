"""
AchieveForms (Firmstep) shared session and lookup helpers.

Many UK council waste-collection sources are built on the AchieveForms
(formerly Firmstep) self-service portal hosted at
``<council>-self.achieveservice.com``.  They all share the same two-step
handshake before data can be retrieved:

1. **Session initialisation** – obtain a ``sid`` (session key) by visiting
   the service landing page and calling ``authapi/isauthenticated``.
   An optional third GET to ``apibroker/domain/<hostname>`` warms the
   session on servers that require it.

2. **Lookup run** – POST to ``apibroker/runLookup`` with the ``sid`` and a
   ``formValues`` payload to retrieve the collection data.

Usage::

    import requests
    from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

    session = requests.Session()
    sid = init_session(
        session,
        initial_url="https://council-self.achieveservice.com/en/service/Bin_days",
        auth_url="https://council-self.achieveservice.com/authapi/isauthenticated",
        hostname="council-self.achieveservice.com",
        auth_test_url="https://council-self.achieveservice.com/apibroker/domain/council-self.achieveservice.com",
    )
    result = run_lookup(
        session,
        api_url="https://council-self.achieveservice.com/apibroker/runLookup",
        sid=sid,
        lookup_id="<lookup_id>",
        form_values={"Section 1": {"UPRN": {"value": "100012345678"}}},
    )
"""

import time

import requests


def init_session(
    session: requests.Session,
    initial_url: str,
    auth_url: str,
    hostname: str,
    *,
    auth_test_url: str | None = None,
    timeout: int = 30,
) -> str:
    """
    Perform the AchieveForms session handshake.

    Steps:
      1. GET ``initial_url`` (follows redirects; the final URL is passed as the
         ``uri`` parameter in the next step).
      2. GET ``auth_url`` with ``uri=<final_url>``, ``hostname=<hostname>``,
         ``withCredentials=true`` → extract ``r.json()["auth-session"]`` as
         the session key (sid).
      3. (Optional) GET ``auth_test_url`` with ``sid=<sid>`` and
         ``_=<timestamp_ms>`` to warm the session / perform a domain check.

    Parameters
    ----------
    session:
        A ``requests.Session`` that will be reused for subsequent API calls.
    initial_url:
        The service landing page URL.  The final URL after any redirects is
        used as the ``uri`` value when fetching the auth endpoint.
    auth_url:
        The ``authapi/isauthenticated`` endpoint URL.
    hostname:
        The AchieveForms hostname (e.g. ``council-self.achieveservice.com``).
    auth_test_url:
        Optional ``apibroker/domain/<hostname>`` URL.  When supplied, a GET
        is made after the auth call to warm the session.
    timeout:
        HTTP request timeout in seconds (default 30).

    Returns
    -------
    str
        The session key (``auth-session`` value) to use in subsequent calls.

    Raises
    ------
    requests.HTTPError
        If any of the HTTP requests returns a non-2xx status code.
    """
    r = session.get(initial_url, timeout=timeout)
    r.raise_for_status()

    params: dict[str, str] = {
        "uri": r.url,
        "hostname": hostname,
        "withCredentials": "true",
    }
    r = session.get(auth_url, params=params, timeout=timeout)
    r.raise_for_status()
    sid: str = r.json()["auth-session"]

    if auth_test_url is not None:
        params_test: dict[str, str | int] = {
            "sid": sid,
            "_": int(time.time() * 1000),
        }
        r = session.get(auth_test_url, params=params_test, timeout=timeout)
        r.raise_for_status()

    return sid


def run_lookup(
    session: requests.Session,
    api_url: str,
    sid: str,
    lookup_id: str,
    form_values: dict,
    *,
    timeout: int = 30,
    no_retry: str = "false",
    app_name: str = "AF-Renderer::Self",
) -> dict:
    """
    POST to ``apibroker/runLookup`` and return the parsed JSON response.

    Parameters
    ----------
    session:
        The ``requests.Session`` previously initialised with
        :func:`init_session`.
    api_url:
        The full ``apibroker/runLookup`` endpoint URL.
    sid:
        The session key obtained from :func:`init_session`.
    lookup_id:
        The AchieveForms lookup identifier (the ``id`` query-string parameter).
    form_values:
        The dictionary to nest under ``"formValues"`` in the JSON request body.
    timeout:
        HTTP request timeout in seconds (default 30).
    no_retry:
        Value for the ``noRetry`` query-string parameter (default ``"false"``).
    app_name:
        Value for the ``app_name`` query-string parameter
        (default ``"AF-Renderer::Self"``).

    Returns
    -------
    dict
        Parsed JSON response from the API.

    Raises
    ------
    requests.HTTPError
        If the HTTP request returns a non-2xx status code.
    """
    params: dict[str, str | int] = {
        "id": lookup_id,
        "repeat_against": "",
        "noRetry": no_retry,
        "getOnlyTokens": "undefined",
        "log_id": "",
        "app_name": app_name,
        "_": int(time.time() * 1000),
        "sid": sid,
    }
    r = session.post(
        api_url,
        params=params,
        json={"formValues": form_values},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()
