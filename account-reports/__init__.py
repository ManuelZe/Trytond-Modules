# -*- coding: utf-8 -*-
"""
    __init__.py

    :copyright: (c) 2024 by Manuel ZE AFE
    :license: see LICENSE for details.
"""
from trytond.pool import Pool


def register():
    Pool.register(
        module='account_report', type_='model'
    )
