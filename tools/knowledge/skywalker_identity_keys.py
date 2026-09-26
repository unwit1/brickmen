#!/usr/bin/env python3
"""Shared parsing for Skywalker Saga character/profile keys.

Most underscore-delimited tokens after the first segment are variant descriptors, but a
small number of source keys use underscores inside the character's canonical identity.
Those cases must be resolved before outfit/version parsing.
"""
from __future__ import annotations

IDENTITY_KEY_OVERRIDES = {
    "Biggs_Darklighter": {
        "base_character_key": "Biggs_Darklighter",
        "canonical_identity_label": "Biggs Darklighter",
        "variant_suffix_tokens": [],
        "reason": "Darklighter is Biggs' surname, not a physical/outfit variant.",
    },
    "Savage_Oppress": {
        "base_character_key": "Savage_Oppress",
        "canonical_identity_label": "Savage Opress",
        "variant_suffix_tokens": [],
        "reason": "The source key splits Savage Opress' full name and misspells Opress as Oppress; treat it as identity, not a variant.",
    },
}

def parse_identity_key(key):
    raw = str(key or "")
    if raw in IDENTITY_KEY_OVERRIDES:
        item = dict(IDENTITY_KEY_OVERRIDES[raw])
        item.update({
            "raw_key": raw,
            "parse_mode": "audited_full_identity_override",
        })
        return item
    parts = raw.split("_")
    return {
        "raw_key": raw,
        "base_character_key": parts[0] if parts else raw,
        "canonical_identity_label": None,
        "variant_suffix_tokens": parts[1:] if len(parts) > 1 else [],
        "parse_mode": "underscore_variant_default",
        "reason": None,
    }
