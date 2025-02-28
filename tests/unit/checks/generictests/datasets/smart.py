#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# fmt: off
# type: ignore

from cmk.base.plugins.agent_based import smart

checkname = 'smart'

parsed = smart.parse_raw_values(
    [[
        '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '5', 'Reallocated_Sector_Ct', '0x0033', '100',
        '100', '010', 'Pre-fail', 'Always', '-', '0'
    ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '9', 'Power_On_Hours', '0x0032', '099',
         '099', '000', 'Old_age', 'Always', '-', '1609'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '12', 'Power_Cycle_Count', '0x0032', '099',
         '099', '000', 'Old_age', 'Always', '-', '9'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '177', 'Wear_Leveling_Count', '0x0013',
         '099', '099', '005', 'Pre-fail', 'Always', '-', '1'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '179', 'Used_Rsvd_Blk_Cnt_Tot', '0x0013',
         '100', '100', '010', 'Pre-fail', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '180', 'Unused_Rsvd_Blk_Cnt_Tot', '0x0013',
         '100', '100', '010', 'Pre-fail', 'Always', '-', '13127'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '181', 'Program_Fail_Cnt_Total', '0x0032',
         '100', '100', '010', 'Old_age', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '182', 'Erase_Fail_Count_Total', '0x0032',
         '100', '100', '010', 'Old_age', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '183', 'Runtime_Bad_Block', '0x0013', '100',
         '100', '010', 'Pre-fail', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '184', 'End-to-End_Error', '0x0033', '100',
         '100', '097', 'Pre-fail', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '187', 'Reported_Uncorrect', '0x0032', '100',
         '100', '000', 'Old_age', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '194', 'Temperature_Celsius', '0x0022',
         '061', '052', '000', 'Old_age', 'Always', '-', '39', '(Min/Max', '31/49)'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '195', 'Hardware_ECC_Recovered', '0x001a',
         '200', '200', '000', 'Old_age', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '197', 'Current_Pending_Sector', '0x0032',
         '100', '100', '000', 'Old_age', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '199', 'UDMA_CRC_Error_Count', '0x003e',
         '100', '100', '000', 'Old_age', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '202', 'Unknown_SSD_Attribute', '0x0033',
         '100', '100', '010', 'Pre-fail', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '235', 'Unknown_Attribute', '0x0012', '099',
         '099', '000', 'Old_age', 'Always', '-', '5'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '241', 'Total_LBAs_Written', '0x0032', '099',
         '099', '000', 'Old_age', 'Always', '-', '7655764477'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '242', 'Total_LBAs_Read', '0x0032', '099',
         '099', '000', 'Old_age', 'Always', '-', '10967739912'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '243', 'Unknown_Attribute', '0x0032', '100',
         '100', '000', 'Old_age', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '244', 'Unknown_Attribute', '0x0032', '100',
         '100', '000', 'Old_age', 'Always', '-', '0'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '245', 'Unknown_Attribute', '0x0032', '100',
         '100', '000', 'Old_age', 'Always', '-', '65535'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '246', 'Unknown_Attribute', '0x0032', '100',
         '100', '000', 'Old_age', 'Always', '-', '65535'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '247', 'Unknown_Attribute', '0x0032', '100',
         '100', '000', 'Old_age', 'Always', '-', '65535'
     ],
     [
         '/dev/sda', 'ATA', 'SAMSUNG_MZ7LM3T8', '251', 'Unknown_Attribute', '0x0032', '100',
         '100', '000', 'Old_age', 'Always', '-', '14938006528'
     ], ['/dev/nvme0n1', 'NVME', 'SAMSUNG_MZQLW960HMJP-00003'],
     ['Critical', 'Warning:', '0x00'], ['Temperature:', '39', 'Celsius'],
     ['Available', 'Spare:', '100%'], ['Available', 'Spare', 'Threshold:', '10%'],
     ['Percentage', 'Used:', '0%'],
     ['Data', 'Units', 'Read:', '5.125.696', '[2,62', 'TB]'],
     ['Data', 'Units', 'Written:', '4.566.369', '[2,33', 'TB]'],
     ['Host', 'Read', 'Commands:', '544.752.409'],
     ['Host', 'Write', 'Commands:', '113.831.833'], ['Controller', 'Busy', 'Time:', '221'],
     ['Power', 'Cycles:', '8'], ['Power', 'On', 'Hours:', '1.609'],
     ['Unsafe', 'Shutdowns:', '5'], ['Media', 'and', 'Data', 'Integrity', 'Errors:', '0'],
     ['Error', 'Information', 'Log', 'Entries:', '0'],
     ['Warning', 'Comp.', 'Temperature', 'Time:', '0'],
     ['Critical', 'Comp.', 'Temperature', 'Time:', '0'],
     ['Temperature', 'Sensor', '1:', '39', 'Celsius']])

discovery = {
    'temp': [('/dev/nvme0n1', {}), ('/dev/sda', {})]
}

checks = {
    'temp': [('/dev/nvme0n1', {
        'levels': (35, 40)
    }, [
        (1, '39 \xb0C (warn/crit at 35/40 \xb0C)', [('temp', 39, 35, 40, None, None)]),
    ]),],
}
