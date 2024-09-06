# -*- coding: utf-8 -*-
"""
    __init__.py

    :copyright: (c) 2024 by Manuel ZE AFE
    :license: see LICENSE for details.
"""
from trytond.pool import Pool
from . import account_report

def register():
    Pool.register(
        account_report.Products_Date,
        account_report.Products_Insurance,
        account_report.Products_Age,
        account_report.Parameters_Load,
        module='account_report', type_='model'
    )

    Pool.register(
        account_report.UpdateSelection,
        module='account_report', type_='wizard')
