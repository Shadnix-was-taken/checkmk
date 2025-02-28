#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# fmt: off
# type: ignore



checkname = 'ibm_svc_mdisk'


info = [['id',
         'status',
         'mode',
         'capacity',
         'encrypt',
         'enclosure_id',
         'over_provisioned',
         'supports_unmap',
         'warning'],
        ['0', 'online', 'array', '20.8TB', 'no', '1', 'no', 'yes', '80']]


discovery = {'': []}
