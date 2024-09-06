from trytond.pool import Pool
from . import reports

__all__ = ['register']


def register():
    Pool.register(
        reports.Products_Age,
        reports.Parameters_Load,
        reports.Products_Date,
        reports.Products_Insurance,
        module='reports', type_='model')
    Pool.register(
        reports.UpdateSelection,
        module='reports', type_='wizard')
    Pool.register(
        module='reports', type_='report')
