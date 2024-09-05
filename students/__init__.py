from trytond.pool import Pool
from . import update_students

__all__ = ['register']


def register():
    Pool.register(
        update_students.UpdateStart,
        update_students.Students,
        module='students', type_='model')
    Pool.register(
        update_students.UpdateStartMAJ,
        update_students.UploadToParty,
        module='students', type_='wizard')
    Pool.register(
        module='students', type_='report')
