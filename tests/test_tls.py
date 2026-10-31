"""Unit tests for ``waste_collection_schedule.tls`` (CA bundles, AIA fallback).

No network: certificates are generated locally (root -> intermediate -> leaf),
and the module's ``fetch_leaf`` / ``download`` / ``trust_roots`` seams are
replaced.
"""

from __future__ import annotations

import datetime
import os
import sys
from types import SimpleNamespace

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.x509.oid import AuthorityInformationAccessOID, NameOID

sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

from waste_collection_schedule import retrievers, tls  # isort:skip

AIA_URL = "http://ca.example.test/intermediate.crt"
HOST = "bins.example.test"
_NOW = datetime.datetime.now(datetime.UTC)


def _name(common_name: str) -> x509.Name:
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])


def _cert(subject, key, issuer, issuer_key, *, ca, san=None, aia=None, ski_of=None):
    builder = (
        x509.CertificateBuilder()
        .subject_name(_name(subject))
        .issuer_name(_name(issuer))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(_NOW - datetime.timedelta(days=1))
        .not_valid_after(_NOW + datetime.timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_key.public_key()),
            critical=False,
        )
    )
    if ca:
        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
    else:
        builder = builder.add_extension(
            x509.ExtendedKeyUsage([x509.ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
    if san:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(san)]), critical=False
        )
    if aia:
        builder = builder.add_extension(
            x509.AuthorityInformationAccess(
                [
                    x509.AccessDescription(
                        AuthorityInformationAccessOID.CA_ISSUERS,
                        x509.UniformResourceIdentifier(aia),
                    )
                ]
            ),
            critical=False,
        )
    return builder.sign(issuer_key, hashes.SHA256())


def _key():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(name="pki")
def fixture_pki():
    root_key, inter_key, leaf_key, other_key = _key(), _key(), _key(), _key()
    root = _cert("Test Root", root_key, "Test Root", root_key, ca=True)
    inter = _cert("Test Intermediate", inter_key, "Test Root", root_key, ca=True)
    leaf = _cert(
        HOST, leaf_key, "Test Intermediate", inter_key, ca=False, san=HOST, aia=AIA_URL
    )
    other_root = _cert("Other Root", other_key, "Other Root", other_key, ca=True)
    # Same name and key as the real intermediate, but signed by a root the
    # trust store does not hold.
    rogue = _cert("Test Intermediate", inter_key, "Other Root", other_key, ca=True)
    return SimpleNamespace(
        root=root, inter=inter, leaf=leaf, other_root=other_root, rogue=rogue
    )


@pytest.fixture(name="seams")
def fixture_seams(monkeypatch, pki):
    """Point the tls seams at the generated PKI; count downloads."""
    tls.clear_cache()
    state = SimpleNamespace(
        downloads=[],
        payload=pki.inter.public_bytes(serialization.Encoding.DER),
        fail=None,
    )

    def download(url):
        state.downloads.append(url)
        if state.fail:
            raise state.fail
        return state.payload

    monkeypatch.setattr(tls, "trust_roots", lambda: [pki.root])
    monkeypatch.setattr(
        tls,
        "fetch_leaf",
        lambda host, port: pki.leaf.public_bytes(serialization.Encoding.DER),
    )
    monkeypatch.setattr(tls, "download", download)
    yield state
    tls.clear_cache()


def _bundle_certs(path):
    with open(path, "rb") as f:
        return x509.load_pem_x509_certificates(f.read())


def test_aia_bundle_completes_and_validates_chain(pki, seams):
    path = tls.aia_bundle(HOST)
    assert seams.downloads == [AIA_URL]
    certs = _bundle_certs(path)
    assert certs[-1] == pki.inter
    # certifi's roots stay in the bundle, the intermediate is only added.
    assert len(certs) > 1


@pytest.mark.parametrize("encoding", ["pem", "pkcs7_der", "pkcs7_pem"])
def test_aia_download_formats(pki, seams, encoding):
    if encoding == "pem":
        seams.payload = pki.inter.public_bytes(serialization.Encoding.PEM)
    else:
        seams.payload = pkcs7.serialize_certificates(
            [pki.inter],
            serialization.Encoding.DER
            if encoding == "pkcs7_der"
            else serialization.Encoding.PEM,
        )
    assert _bundle_certs(tls.aia_bundle(HOST))[-1] == pki.inter


def test_aia_bundle_rejects_hostname_mismatch(seams):
    with pytest.raises(tls.IncompleteChainError) as err:
        tls.aia_bundle("other.example.test")
    assert err.value.host == "other.example.test"
    assert "does not validate" in err.value.reason


def test_aia_bundle_rejects_untrusted_intermediate(pki, seams):
    seams.payload = pki.rogue.public_bytes(serialization.Encoding.DER)
    with pytest.raises(tls.IncompleteChainError, match="does not validate"):
        tls.aia_bundle(HOST)


def test_aia_bundle_reports_failed_download(seams):
    seams.fail = OSError("HTTP Error 500")
    with pytest.raises(tls.IncompleteChainError) as err:
        tls.aia_bundle(HOST)
    assert HOST in str(err.value)
    assert AIA_URL in err.value.reason
    assert "HTTP Error 500" in err.value.reason


def test_aia_bundle_needs_ca_issuers(monkeypatch, pki, seams):
    bare = _cert(HOST, _key(), "Test Intermediate", _key(), ca=False, san=HOST)
    monkeypatch.setattr(
        tls,
        "fetch_leaf",
        lambda host, port: bare.public_bytes(serialization.Encoding.DER),
    )
    with pytest.raises(tls.IncompleteChainError, match="no caIssuers"):
        tls.aia_bundle(HOST)
    assert seams.downloads == []


def test_aia_bundle_is_cached_per_host(seams):
    first = tls.aia_bundle(HOST)
    assert tls.aia_bundle(HOST.upper()) == first
    assert seams.downloads == [AIA_URL]


class _Chain(Exception):
    pass


def _session(fail_until_verify):
    calls = []

    def send(url, **kwargs):
        calls.append(kwargs.get("verify", True))
        if fail_until_verify and "verify" not in kwargs:
            raise _Chain(
                "curl: (60) SSL certificate OpenSSL verify result: "
                "unable to get local issuer certificate (20)"
            )
        return SimpleNamespace(status_code=200, url=url, raise_for_status=lambda: None)

    return send, calls


def test_send_retries_once_with_aia_bundle_then_uses_cache(seams):
    send, calls = _session(fail_until_verify=True)
    url = f"https://{HOST}/api"
    assert tls.send(send, url, tls.AIA).status_code == 200
    bundle = calls[-1]
    assert calls == [True, bundle] and bundle.endswith(".pem")
    tls.send(send, url, tls.AIA)
    assert calls[-1] == bundle and len(calls) == 3
    assert seams.downloads == [AIA_URL]


def test_send_without_chain_problem_never_touches_aia(seams):
    send, calls = _session(fail_until_verify=False)
    tls.send(send, f"https://{HOST}/api", tls.AIA)
    assert calls == [True]
    assert seams.downloads == []


def test_send_reraises_other_tls_errors_unchanged(seams):
    def send(url, **kwargs):
        raise _Chain("certificate has expired")

    with pytest.raises(_Chain, match="expired"):
        tls.send(send, f"https://{HOST}/", tls.AIA)
    assert seams.downloads == []


def test_send_never_falls_back_to_unverified(seams):
    seams.fail = OSError("blocked")
    send, calls = _session(fail_until_verify=True)
    with pytest.raises(tls.IncompleteChainError, match="blocked"):
        tls.send(send, f"https://{HOST}/", tls.AIA)
    assert False not in calls


def test_send_passes_plain_verify_values_through():
    send, calls = _session(fail_until_verify=False)
    tls.send(send, "https://x.test/", True)
    tls.send(send, "https://x.test/", "bundle.pem")
    tls.send(send, "https://x.test/", False)
    assert calls == [True, "bundle.pem", False]


def test_is_incomplete_chain_follows_wrapped_exceptions():
    try:
        try:
            raise OSError("[SSL] unable to verify the first certificate")
        except OSError as inner:
            raise RuntimeError("request failed") from inner
    except RuntimeError as outer:
        assert tls.is_incomplete_chain(outer)
    assert not tls.is_incomplete_chain(RuntimeError("certificate has expired"))


def test_request_step_uses_aia(seams):
    send, calls = _session(fail_until_verify=True)
    source = SimpleNamespace(params={}, session=SimpleNamespace(get=send, post=send))
    step = retrievers.Request(f"https://{HOST}/api", verify=tls.AIA)
    assert step(source).status_code == 200
    assert calls[0] is True and calls[1].endswith(".pem")


def test_ca_bundle_reexported_for_aura_sources():
    from waste_collection_schedule.service import SalesforceAuraApex

    assert SalesforceAuraApex.ca_bundle is tls.ca_bundle
