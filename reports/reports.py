# -*- coding: utf-8 -*-
"""
    account_report.py

    :copyright: (c) 2024 by Manuel ZE AFE
    :license: see LICENSE for more details.
"""
from trytond.model import ModelSQL, fields, ModelView
from trytond.pyson import If, Bool, Eval
from trytond.wizard import Wizard, StateAction, StateView, StateTransition
from datetime import datetime
from trytond.pool import Pool
from dateutil.relativedelta import relativedelta
from trytond.transaction import Transaction

class Products_Date(ModelSQL, ModelView):
    "Number of times a product is used over a period of time"
    __name__ = 'products.number.reports'
    _rec_name = 'product'

    product = fields.Char("Produits")
    nombre = fields.Integer("Nombre")
    prix_u = fields.Float("Prix Unitaire")
    prix_t = fields.Float("Prix Total")

class Products_Insurance(ModelSQL, ModelView) :
    "Products number by insurance"
    __name__ = 'products.insurance'
    _recname = 'product'

    product = fields.Char("Produits")
    nombre = fields.Integer("Nombre")

class Products_Age(ModelSQL, ModelView):
    "Products classement by Age"
    __name__ = 'products.age'
    _recname = 'product'

    product = fields.Char("Produits")
    average_age = fields.Float("Age Moyen")
    min_age = fields.Integer("Age Minimum")
    max_age = fields.Integer("Age Maximun")


class Parameters_Load(ModelSQL, ModelView) :
    " Parameters of all requests "
    __name__ = 'parameters.reports'
    _rec_name = 'products'

    start_date = fields.Date("Date de Début", required=True)
    end_date = fields.Date("Date de fin", required=True)
    product = fields.Many2One(
        'product.product', "Produit", select=True,
        help="The product that defines the common properties "
        "inherited by the variant.")
    assurance = fields.Many2One(
        'party.party', "Assurance",
        required=False, select=True,
        domain=[
            If(Eval('is_insurance_company'), ('is_insurance_company', '=', True), ()),
            ],
        depends=['is_insurance_company'],
        help="The insurance Company used to generate the report.")
    by_age = fields.Boolean("Classement Par Âge")
    by_date = fields.Boolean("Classement Par Date")
    by_insurance = fields.Boolean("Classement Par Assurance")

class UpdateSelection(Wizard):
    "Wizard to update easily the The Selected Report"
    __name__ = 'parameters.reports.start'

    start_state = 'open_'
    open_ = StateAction('reports.act_update_parameters_verify')

    def age(dob):
        today = datetime.today().date()
        if dob:
            start = datetime.strptime(str(dob), '%Y-%m-%d')
            end = datetime.strptime(str(today), '%Y-%m-%d')

            rdelta = relativedelta(end, start)

            years_months_days = str(rdelta.years) + 'y ' \
                + str(rdelta.months) + 'm ' \
                + str(rdelta.days) + 'd'
        
        return rdelta.years

        
    @staticmethod
    def do_open_(self):

        pool = Pool()
        R_parameters = pool.get('parameters.reports')
        Invoice = pool.get("account.invoice")

        results = []
        all_parameters = R_parameters.browse(Transaction().context.get('active_ids'))
        for parameter in all_parameters:
            if parameter.by_age :
                Results = pool.get("products.age")
                Requests = pool.get("account.invoice.line")

                invoice_lines = Requests.search([('create_date'.strftime("%Y-%m-%d"), 'in', (parameter.start_date, parameter.end_date)), ('product.description', '=', parameter.product)])

                dict_of_product_age = {}
                # Format de la liste des éléments
                # [age_moyen, age_minimum, age_maximum]
                list_of_element = []
                for invoice_line in invoice_lines:
                    list_of_age = []
                    inv = Invoice(invoice_line.invoice)
                    if dict_of_product_age == {} :
                        list_of_age.append(self.age(inv.party.dob))
                        dict_of_product_age[invoice_line.product.template.name] = list_of_age
                    else :
                        if invoice_line.product.template.name in dict_of_product_age :
                            dict_of_product_age[invoice_line.product.template.name].append(self.age(inv.party.dob))
                        else :
                            list_of_age.append(self.age(inv.party.dob))
                            dict_of_product_age[invoice_line.product.template.name] = list_of_age

                for elt in dict_of_product_age :
                    age_moyen = sum(dict_of_product_age[elt]) / len(dict_of_product_age[elt])
                    minimum = min(dict_of_product_age[elt])
                    maximum = max(dict_of_product_age[elt])

                    list_of_element = [age_moyen, minimum, maximum]

                    dict_of_product_age[elt] = list_of_element

                    results = []
                    result1 = {
                        'product' : elt,
                        'average_age' : age_moyen,
                        'min_age' : minimum,
                        'max_age' : maximum,
                    }
                    results.append(result1)
                    Results.create(results)

                    return results





