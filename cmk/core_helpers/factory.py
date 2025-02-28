#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import logging

from cmk.snmplib.type_defs import SNMPBackend, SNMPBackendEnum, SNMPHostConfig

from .snmp_backend import ClassicSNMPBackend, StoredWalkSNMPBackend

try:
    from .cee.snmp_backend import inline  # type: ignore[import]
except ImportError:
    inline = None  # type: ignore[assignment]

__all__ = ["backend"]

_force_stored_walks = False


def force_stored_walks() -> None:
    global _force_stored_walks
    _force_stored_walks = True


def get_force_stored_walks() -> bool:
    return _force_stored_walks


def backend(
    snmp_config: SNMPHostConfig, logger: logging.Logger, *, use_cache: bool | None = None
) -> SNMPBackend:
    if use_cache is None:
        use_cache = get_force_stored_walks()

    if use_cache or snmp_config.snmp_backend is SNMPBackendEnum.STORED_WALK:
        return StoredWalkSNMPBackend(snmp_config, logger)

    if inline and snmp_config.snmp_backend is SNMPBackendEnum.INLINE:
        return inline.InlineSNMPBackend(snmp_config, logger)

    if snmp_config.snmp_backend is SNMPBackendEnum.CLASSIC:
        return ClassicSNMPBackend(snmp_config, logger)

    raise NotImplementedError(f"Unknown SNMP backend: {snmp_config.snmp_backend}")
