"""mTLS client-cert provider.

Loads a client certificate + private key (optionally a separate CA bundle)
and produces an `ssl.SSLContext` configured for mTLS. The context is
cached for the provider's lifetime — certificates on disk rotate via
the same mechanism that deploys them, so there is no TTL to track here.
"""
from __future__ import annotations

import os
import ssl
import threading
from dataclasses import dataclass, field
from pathlib import Path

from .base import CredentialProvider, ResolvedCredential


@dataclass
class MTLSClientProvider(CredentialProvider):
    profile: str = "mtls"
    cert_path: str = ""
    key_path: str = ""
    key_password_env: str | None = None
    ca_bundle_path: str | None = None
    # When set, a subjectAlternativeName or commonName the peer must present.
    server_hostname: str | None = None

    _cached_ctx: ssl.SSLContext | None = field(default=None, init=False, repr=False, compare=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False, compare=False)

    def resolve(self, system: str) -> ResolvedCredential:
        with self._lock:
            if self._cached_ctx is None:
                self._cached_ctx = self._build_context(system)
            ctx = self._cached_ctx
        return ResolvedCredential(
            system=system,
            profile=self.profile,
            headers={},  # mTLS is transport-layer; no Authorization header
            tls_context=ctx,
            metadata={
                "cert_path": self.cert_path,
                "ca_bundle_path": self.ca_bundle_path,
                "server_hostname": self.server_hostname,
            },
        )

    def _build_context(self, system: str) -> ssl.SSLContext:
        for label, path in (("cert_path", self.cert_path), ("key_path", self.key_path)):
            if not path:
                raise RuntimeError(f"mtls profile for {system} requires {label}")
            if not Path(path).is_file():
                raise RuntimeError(f"mtls profile for {system}: {label}='{path}' not found")
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if self.ca_bundle_path:
            ctx.load_verify_locations(cafile=self.ca_bundle_path)
        password = None
        if self.key_password_env:
            password = os.environ.get(self.key_password_env) or None
        ctx.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path, password=password)
        ctx.check_hostname = bool(self.server_hostname)
        ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx
