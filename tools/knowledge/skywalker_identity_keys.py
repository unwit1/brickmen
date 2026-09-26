#!/usr/bin/env python3
"""Shared parsing for Skywalker Saga character/profile keys.

Most underscore-delimited tokens after the first segment are variant descriptors, but a
small number of source keys use underscores inside the character's canonical identity.
Those cases must be resolved before outfit/version parsing.
"""
from __future__ import annotations

SPECIALIZED_ROLE_MATCH_OVERRIDES = {
    "Stormtrooper_FirstOrder_Ep9_Jet_Trooper": {
        "required_catalog_semantic_tokens": ["firstorder", "jet", "trooper"],
        "reason": "The source key specializes generic Stormtrooper into the physical catalog role First Order Jet Trooper; the specialized role legitimately replaces the base noun.",
    },
}

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
    "Rey_Skywalker": {
        "base_character_key": "Rey",
        "canonical_identity_label": "Rey Skywalker",
        "variant_suffix_tokens": [],
        "reason": "Skywalker is part of Rey's final canonical game identity, not an outfit or appearance suffix. Keep the broader Rey base for physical-family matching.",
    },
    "Rebel_Friend": {
        "base_character_key": "Rebel_Friend",
        "canonical_identity_label": "Rebel Friend",
        "variant_suffix_tokens": [],
        "reason": "Rebel Friend is a named playable character identity in The Skywalker Saga, not a generic Rebel role with a Friend variant.",
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

def specialized_role_match(key):
    """Return audited role-specialization matching metadata, if any."""
    item = SPECIALIZED_ROLE_MATCH_OVERRIDES.get(str(key or ""))
    return dict(item) if item else None
