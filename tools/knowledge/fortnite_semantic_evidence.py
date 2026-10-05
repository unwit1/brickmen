"""Shared exact-evidence identity for semantic comparison and promotion gates."""
from __future__ import annotations

import re

HASH = re.compile(r"[0-9a-fA-F]{64}\Z")


def evidence_identity(record):
    evidence = record.get("evidence") or {}
    values = [evidence.get("source_image_sha256"), evidence.get("lego_image_sha256")]
    if any(not isinstance(value, str) or not HASH.fullmatch(value) for value in values):
        return None
    scope = evidence.get("evidence_scope")
    if not isinstance(scope, str) or not scope or evidence.get("claims_unobserved_surfaces") is not False:
        return None
    return (values[0].lower(), values[1].lower(), scope)


def require_shared_evidence(records):
    identities = [evidence_identity(record) for record in records]
    if not identities or any(identity is None for identity in identities):
        raise ValueError("Reviews require exact source/LEGO hashes and observed evidence scope")
    if len(set(identities)) != 1:
        raise ValueError("Reviews refer to different exact evidence bytes or scopes")
    return identities[0]
