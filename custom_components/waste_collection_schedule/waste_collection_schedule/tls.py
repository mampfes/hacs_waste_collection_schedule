"""TLS trust helpers: completed CA bundles and the AIA fallback.

Some provider hosts send their leaf certificate without the intermediate that
issued it. Browsers repair that on the fly (they download the missing
certificate from the leaf's *Authority Information Access* ``caIssuers`` URL,
or already know it), so the site looks fine to its users; non-browser clients
like ours fail with "unable to get local issuer certificate". The fix is never
``verify=False``: it is to complete the chain.

Two ways to do it:

* :func:`ca_bundle` -- certifi's roots plus a PEM the source ships. Simple,
  but the pinned intermediate has to be replaced whenever the host renews
  under a different one.
* :data:`AIA` -- what a browser does. Pass ``verify=tls.AIA`` to a declared
  :class:`~waste_collection_schedule.retrievers.Request` /
  :class:`~waste_collection_schedule.retrievers.Lookup`. The request is first
  sent with normal verification. Only if that fails because the chain is
  incomplete does :func:`aia_bundle` read the host's leaf, download the
  issuer named in its ``caIssuers`` URL (DER, PEM or PKCS#7; plain HTTP is
  allowed, as for browsers), validate leaf plus intermediate against certifi's
  roots *and the host name* with ``cryptography``'s verifier, and retry once
  with ``verify=<certifi + that intermediate>``. The bundle is cached per host
  for the life of the process.

Why downloading over plain HTTP is safe: the downloaded certificate is only
used after it was shown to be a CA certificate signed (directly or through
further downloaded CA certificates) by a root certifi already trusts, and to
chain the host's own leaf for that host name. An attacker who swaps the
download can make the fallback fail, never make an untrusted certificate
trusted. The retried request is then verified by the HTTP client itself, as
any other request: the bundle still ends in certifi's self-signed roots, so an
added intermediate extends no trust the web PKI did not already grant.

Nothing here ever falls back to ``verify=False``: a failed repair raises
:class:`IncompleteChainError` naming the host and the reason.
"""

from __future__ import annotations

import hashlib
import ipaddress
import logging
import os
import socket
import ssl
import tempfile
import threading
import urllib.request
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import urlsplit

import certifi

if TYPE_CHECKING:
    from cryptography import x509

_LOGGER = logging.getLogger(__name__)

# Messages OpenSSL / BoringSSL (curl_cffi) and Python's ssl module give for a
# chain the client cannot complete. Anything else (expired, wrong host name,
# self-signed) is not an AIA case and is re-raised unchanged.
_INCOMPLETE_CHAIN_MESSAGES: Final = (
    "unable to get local issuer certificate",
    "unable to verify the first certificate",
)
# Bounds on what the fallback will do for one host.
_MAX_AIA_HOPS: Final = 3
_MAX_DOWNLOAD_BYTES: Final = 64 * 1024
_TIMEOUT: Final = 15


class AiaVerify:
    """Marker type of :data:`AIA` (``verify=tls.AIA``)."""

    _instance: AiaVerify | None = None

    def __new__(cls) -> AiaVerify:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "tls.AIA"


AIA: Final = AiaVerify()
"""``verify=tls.AIA``: verify normally, complete an incomplete chain via AIA."""

type Verify = bool | str | AiaVerify


class IncompleteChainError(Exception):
    """The host's certificate chain is incomplete and could not be completed."""

    def __init__(self, host: str, reason: str):
        self.host = host
        self.reason = reason
        super().__init__(
            f"TLS: {host} does not send its intermediate certificate and the "
            f"AIA fallback could not complete the chain: {reason}"
        )


# --- Completed CA bundles ----------------------------------------------------

_bundles: dict[str, str] = {}
_bundles_lock = threading.Lock()


def ca_bundle(extra_pem: str) -> str:
    """Path of a CA bundle: certifi's roots plus ``extra_pem`` (a PEM text).

    Written once per process to a temp file and reused.
    """
    key = hashlib.sha256(extra_pem.encode("ascii")).hexdigest()
    with _bundles_lock:
        path = _bundles.get(key)
        if path is not None and os.path.exists(path):
            return path
        with open(certifi.where(), encoding="ascii") as f:
            roots = f.read()
        fd, path = tempfile.mkstemp(prefix="wcs_ca_", suffix=".pem")
        with os.fdopen(fd, "w", encoding="ascii") as f:
            f.write(roots)
            f.write("\n")
            f.write(extra_pem)
        _bundles[key] = path
        return path


# --- AIA fallback --------------------------------------------------------------

_aia_bundles: dict[tuple[str, int], str] = {}
_aia_lock = threading.Lock()


def is_incomplete_chain(exc: BaseException) -> bool:
    """Whether ``exc`` (or an exception it wraps) is an incomplete-chain failure."""
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        text = str(current).lower()
        if any(message in text for message in _INCOMPLETE_CHAIN_MESSAGES):
            return True
        current = current.__cause__ or current.__context__
    return False


def _fetch_leaf(host: str, port: int) -> bytes:
    """The DER leaf certificate ``host`` presents, read without verification.

    Unverified on purpose: this is the certificate whose chain is about to be
    checked, and nothing read here is trusted until :func:`_validate` passed.
    """
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # nosec B501
    with (
        socket.create_connection((host, port), timeout=_TIMEOUT) as sock,
        context.wrap_socket(sock, server_hostname=host) as tls_sock,
    ):
        der = tls_sock.getpeercert(binary_form=True)
    if not der:
        raise IncompleteChainError(host, "the server presented no certificate")
    return der


def _download(url: str) -> bytes:
    """GET a ``caIssuers`` URL (http or https), capped in size."""
    if urlsplit(url).scheme not in ("http", "https"):
        raise ValueError(f"unsupported caIssuers URL scheme: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:  # nosec B310
        data = response.read(_MAX_DOWNLOAD_BYTES + 1)
    if len(data) > _MAX_DOWNLOAD_BYTES:
        raise ValueError(f"caIssuers download larger than {_MAX_DOWNLOAD_BYTES} bytes")
    return data


def _trust_roots() -> list[x509.Certificate]:
    from cryptography import x509

    with open(certifi.where(), "rb") as f:
        return x509.load_pem_x509_certificates(f.read())


# Seams for the tests: no network and a private root in unit tests.
fetch_leaf: Callable[[str, int], bytes] = _fetch_leaf
download: Callable[[str], bytes] = _download
trust_roots: Callable[[], list[Any]] = _trust_roots


def _load_certificates(data: bytes) -> list[x509.Certificate]:
    """Certificates in a ``caIssuers`` download: DER, PEM or PKCS#7."""
    from cryptography import x509
    from cryptography.hazmat.primitives.serialization import pkcs7

    if b"-----BEGIN PKCS7-----" in data:
        return pkcs7.load_pem_pkcs7_certificates(data)
    if b"-----BEGIN CERTIFICATE-----" in data:
        return x509.load_pem_x509_certificates(data)
    try:
        return [x509.load_der_x509_certificate(data)]
    except ValueError:
        return pkcs7.load_der_pkcs7_certificates(data)


def _ca_issuers(cert: x509.Certificate) -> list[str]:
    from cryptography import x509
    from cryptography.x509.oid import AuthorityInformationAccessOID

    try:
        aia = cert.extensions.get_extension_for_class(
            x509.AuthorityInformationAccess
        ).value
    except x509.ExtensionNotFound:
        return []
    return [
        str(description.access_location.value)
        for description in aia
        if description.access_method == AuthorityInformationAccessOID.CA_ISSUERS
        and isinstance(description.access_location, x509.UniformResourceIdentifier)
    ]


def _subject(host: str) -> Any:
    from cryptography import x509

    try:
        return x509.IPAddress(ipaddress.ip_address(host))
    except ValueError:
        return x509.DNSName(host)


def _validate(
    host: str, leaf: x509.Certificate, intermediates: list[x509.Certificate]
) -> list[x509.Certificate]:
    """The verified chain (leaf first, root last); raise unless ``leaf`` chains
    to a trusted root for ``host``."""
    from cryptography.x509 import verification

    store = verification.Store(trust_roots())
    verifier = (
        verification.PolicyBuilder().store(store).build_server_verifier(_subject(host))
    )
    return verifier.verify(leaf, intermediates)


def _complete_chain(host: str, port: int) -> list[x509.Certificate]:
    """The intermediates on ``host``'s verified chain (no leaf, no root).

    Only certificates of the chain the verifier built are returned; extra
    certificates in a download never reach the bundle.
    """
    try:
        from cryptography import x509
        from cryptography.x509 import verification
    except ImportError as exc:  # cryptography < 42 has no verifier
        raise IncompleteChainError(
            host, f"the 'cryptography' verification API is unavailable ({exc})"
        ) from exc

    try:
        leaf = x509.load_der_x509_certificate(fetch_leaf(host, port))
    except IncompleteChainError:
        raise
    except Exception as exc:
        raise IncompleteChainError(
            host, f"could not read its certificate ({exc})"
        ) from exc

    intermediates: list[x509.Certificate] = []
    current = leaf
    last_error = "the certificate names no caIssuers URL"
    for _ in range(_MAX_AIA_HOPS):
        urls = _ca_issuers(current)
        if not urls:
            break
        fetched: list[x509.Certificate] = []
        for url in urls:
            try:
                fetched = _load_certificates(download(url))
            except Exception as exc:
                last_error = f"downloading {url} failed ({exc})"
                continue
            if fetched:
                break
            last_error = f"{url} held no certificate"
        if not fetched:
            break
        intermediates.extend(fetched)
        try:
            chain = _validate(host, leaf, intermediates)
        except verification.VerificationError as exc:
            last_error = f"the chain does not validate ({exc})"
            current = fetched[0]
            continue
        return list(chain[1:-1])
    raise IncompleteChainError(host, last_error)


def aia_bundle(host: str, port: int = 443) -> str:
    """Path of certifi's roots plus ``host``'s validated AIA intermediates.

    Cached per host and port for the life of the process. Raises
    :class:`IncompleteChainError` when the chain cannot be completed.
    """
    key = (host.lower(), port)
    with _aia_lock:
        path = _aia_bundles.get(key)
        if path is not None and os.path.exists(path):
            return path
        from cryptography.hazmat.primitives.serialization import Encoding

        intermediates = _complete_chain(host, port)
        pem = "".join(
            c.public_bytes(Encoding.PEM).decode("ascii") for c in intermediates
        )
        path = ca_bundle(pem)
        _aia_bundles[key] = path
        _LOGGER.info(
            "TLS: %s omits its intermediate certificate; completed the chain "
            "via AIA (%s)",
            host,
            ", ".join(c.subject.rfc4514_string() for c in intermediates),
        )
        return path


def send(
    send_request: Callable[..., Any], url: str, verify: Verify, **kwargs: Any
) -> Any:
    """Call ``send_request(url, verify=..., **kwargs)``, honouring :data:`AIA`.

    ``send_request`` is a session's ``get`` or ``post``. A boolean or a bundle
    path is passed through unchanged (``True`` is not passed at all, so a
    session's own default applies). With :data:`AIA` the request goes out
    with normal verification first, or straight with a bundle cached for the
    host; an incomplete-chain failure is repaired once via :func:`aia_bundle`.
    """
    if not isinstance(verify, AiaVerify):
        if verify is not True:
            kwargs["verify"] = verify
        return send_request(url, **kwargs)
    parts = urlsplit(url)
    host = parts.hostname or ""
    port = parts.port or 443
    cached = _aia_bundles.get((host.lower(), port))
    if cached is not None and os.path.exists(cached):
        try:
            return send_request(url, verify=cached, **kwargs)
        except Exception as exc:
            if parts.scheme != "https" or not is_incomplete_chain(exc):
                raise
            # Stale bundle (the host renewed under another intermediate):
            # evict it and run the normal repair path once.
            with _aia_lock:
                if _aia_bundles.get((host.lower(), port)) == cached:
                    del _aia_bundles[(host.lower(), port)]
    try:
        return send_request(url, **kwargs)
    except Exception as exc:
        if parts.scheme != "https" or not is_incomplete_chain(exc):
            raise
        bundle = aia_bundle(host, port)
    return send_request(url, verify=bundle, **kwargs)


def clear_cache() -> None:
    """Forget the AIA bundles of this process (tests)."""
    with _aia_lock:
        _aia_bundles.clear()
