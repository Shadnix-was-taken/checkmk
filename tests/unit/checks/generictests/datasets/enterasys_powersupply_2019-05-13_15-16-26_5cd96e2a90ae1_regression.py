#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# fmt: off
# type: ignore



checkname = 'enterasys_powersupply'


info = [['101', '3', '1', '1'], ['102', '', '', '1']]


discovery = {'': [('101', {})]}


checks = {'': [('101',
                {'redundancy_ok_states': [1]},
                [(0, 'Status: working and redundant (ac-dc)', [])])]}
