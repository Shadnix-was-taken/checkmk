#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from cmk.gui.i18n import _
from cmk.gui.plugins.wato.utils import (
    CheckParameterRulespecWithItem,
    rulespec_registry,
    RulespecGroupCheckParametersApplications,
)
from cmk.gui.valuespec import Age, Dictionary, TextInput, Tuple


def _parameter_valuespec_oracle_recovery_status():
    return Dictionary(
        elements=[
            (
                "levels",
                Tuple(
                    title=_("Levels for checkpoint time"),
                    elements=[
                        Age(title=_("warning if higher then"), default_value=1800),
                        Age(title=_("critical if higher then"), default_value=3600),
                    ],
                ),
            ),
            (
                "backup_age",
                Tuple(
                    title=_("Levels for user managed backup files"),
                    help=_(
                        "Important! This checks is only for monitoring of datafiles "
                        "who were left in backup mode. "
                        "(alter database datafile ... begin backup;) "
                    ),
                    elements=[
                        Age(title=_("warning if higher then"), default_value=1800),
                        Age(title=_("critical if higher then"), default_value=3600),
                    ],
                ),
            ),
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="oracle_recovery_status",
        group=RulespecGroupCheckParametersApplications,
        item_spec=lambda: TextInput(title=_("Database SID"), size=12, allow_empty=False),
        match_type="dict",
        parameter_valuespec=_parameter_valuespec_oracle_recovery_status,
        title=lambda: _("Oracle Recovery Status"),
    )
)
