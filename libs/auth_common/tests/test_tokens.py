"""Pruebas del núcleo puro de tokens: firma, expiración y, sobre todo, que un
token emitido para un servicio no sirva para autenticarse contra otro (aud).
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from auth_common.errors import AudienceError, ExpiredTokenError, InvalidTokenError
from auth_common.tokens import decode_token, encode_token

SECRET = "clave-de-pruebas"
ALGORITHM = "HS256"
ISSUER = "auth-service"
SUBJECT = "11111111-1111-1111-1111-111111111111"


def _issue(**overrides):
    params = dict(
        subject=SUBJECT,
        username="ana",
        role="user",
        audience=["auth-service"],
        secret=SECRET,
        algorithm=ALGORITHM,
        issuer=ISSUER,
        expires_in=timedelta(minutes=5),
    )
    params.update(overrides)
    return encode_token(**params)


def test_round_trip_decode_returns_claims():
    token, expires_at = _issue()

    claims = decode_token(
        token, secret=SECRET, algorithm=ALGORITHM, issuer=ISSUER,
        expected_audience="auth-service",
    )

    assert claims.sub == SUBJECT
    assert claims.username == "ana"
    assert claims.role == "user"
    assert claims.aud == ("auth-service",)
    assert claims.expires_at == expires_at


def test_expired_token_raises():
    token, _ = _issue(expires_in=timedelta(seconds=-1))

    with pytest.raises(ExpiredTokenError):
        decode_token(token, secret=SECRET, algorithm=ALGORITHM, issuer=ISSUER)


def test_wrong_signature_raises():
    token, _ = _issue()

    with pytest.raises(InvalidTokenError):
        decode_token(token, secret="otra-clave", algorithm=ALGORITHM, issuer=ISSUER)


def test_garbage_token_raises_invalid_token():
    with pytest.raises(InvalidTokenError):
        decode_token("no-es-un-jwt", secret=SECRET, algorithm=ALGORITHM, issuer=ISSUER)


def test_audience_mismatch_rejected_in_both_directions():
    """Un token emitido para auth-service no debe validar contra
    products-service, y viceversa — es la prueba central del Requerimiento
    9(b): 'un token emitido para un servicio no debe servir en otro'."""
    token_for_auth, _ = _issue(audience=["auth-service"])
    token_for_products, _ = _issue(audience=["products-service"])

    decode_token(token_for_auth, secret=SECRET, algorithm=ALGORITHM, issuer=ISSUER,
                 expected_audience="auth-service")
    with pytest.raises(AudienceError):
        decode_token(token_for_products, secret=SECRET, algorithm=ALGORITHM, issuer=ISSUER,
                     expected_audience="auth-service")

    decode_token(token_for_products, secret=SECRET, algorithm=ALGORITHM, issuer=ISSUER,
                 expected_audience="products-service")
    with pytest.raises(AudienceError):
        decode_token(token_for_auth, secret=SECRET, algorithm=ALGORITHM, issuer=ISSUER,
                     expected_audience="products-service")


def test_token_with_multiple_audiences_validates_against_each_member():
    token, _ = _issue(audience=["auth-service", "products-service"])

    for audience in ("auth-service", "products-service"):
        claims = decode_token(token, secret=SECRET, algorithm=ALGORITHM, issuer=ISSUER,
                              expected_audience=audience)
        assert audience in claims.aud

    with pytest.raises(AudienceError):
        decode_token(token, secret=SECRET, algorithm=ALGORITHM, issuer=ISSUER,
                     expected_audience="otro-servicio")


def test_decode_without_expected_audience_skips_audience_check():
    """`web` decodifica localmente solo para leer `role`; no es un
    resource server y no debe exigir audiencia."""
    token, _ = _issue(audience=["products-service"])

    claims = decode_token(token, secret=SECRET, algorithm=ALGORITHM, issuer=ISSUER)

    assert claims.aud == ("products-service",)
