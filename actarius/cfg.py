"""Configuration for actarius."""

import os

import birch


class CfgKey():
    PRINT_STACKTRACE = 'PRINT_STACKTRACE'


CFG = birch.Birch(
    namespace='actarius',
    defaults={
        CfgKey.PRINT_STACKTRACE: 'False'
    },
    default_casters={
        CfgKey.PRINT_STACKTRACE: birch.casters.true_false_caster,
    },
)


PRINT_STACKTRACE = CFG[CfgKey.PRINT_STACKTRACE]

TEMP_DIR = CFG.xdg_cache_dpath()
os.makedirs(TEMP_DIR, exist_ok=True)
