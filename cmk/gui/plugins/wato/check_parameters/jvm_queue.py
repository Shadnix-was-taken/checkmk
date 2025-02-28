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
from cmk.gui.valuespec import Integer, TextInput, Tuple


def _item_spec_jvm_queue():
    return TextInput(
        title=_("Name of the virtual machine"),
        help=_("The name of the application server"),
        allow_empty=False,
    )


def _parameter_valuespec_jvm_queue():
    return Tuple(
        help=_(
            "The BEA application servers have 'Execute Queues' "
            "in which requests are processed. This rule allows to set "
            "warn and crit levels for the number of requests that are "
            "being queued for processing."
        ),
        elements=[
            Integer(
                title=_("Warning at"),
                unit=_("requests"),
                default_value=20,
            ),
            Integer(
                title=_("Critical at"),
                unit=_("requests"),
                default_value=50,
            ),
        ],
    )


rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="jvm_queue",
        group=RulespecGroupCheckParametersApplications,
        item_spec=_item_spec_jvm_queue,
        parameter_valuespec=_parameter_valuespec_jvm_queue,
        title=lambda: _("JVM Execute Queue Count"),
    )
)
