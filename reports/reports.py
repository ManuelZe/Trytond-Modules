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
import json

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

class Results_Details(ModelSQL, ModelView):
    "Les différents détails de presques tout"
    __name__ = 'results.details'
    _recname = 'patient'

    patient = fields.Char("Patient")
    facture = fields.Char("Numero de Facture")
    product = fields.Char("Produit")
    prescriptor = fields.Char("Prescripteur")
    category = fields.Char("Categorie")


class Prescriptors_Patients(ModelSQL, ModelView):
    "Classement des Prescripteurs par patients"
    __name__ = 'prescriptors.patients'
    _recname = 'prescriptor'

    prescriptor = fields.Char('Prescripteur')
    nombre = fields.Float("Nombre de patients")
    dict_prescriptor_patient = fields.Dict(fields.Char("Données Identiques"), "Prescriptors")

class Parameters_Load(ModelSQL, ModelView) :
    " Parameters of all requests "
    __name__ = 'parameters.reports'
    _rec_name = 'product'

    start_date = fields.DateTime("Date de Début", required=True)
    end_date = fields.DateTime("Date de fin", required=True)
    product = fields.Many2One(
        'product.product', "Produit", select=True,
        help="The product that defines the common properties "
        "inherited by the variant.")
    category = fields.Many2One(
        'product.category', "Categorie des Produits",
        required=False, select=True,
        help="La Catégorie Utilisée Pour le classement."
    )
    subcategory = fields.Many2One(
        'product.category', 'Sous-catégorie',
        domain=[('parent', '!=', None)]
    )
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
    by_prescriptor = fields.Boolean("Classement Par Prescripteurs")
    by_category = fields.Boolean("Classement Par Catégorie")


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
            if parameter.by_category :
                Product = pool.get('product.product')
                InvoiceLine = pool.get('account.invoice.line')
                Invoice = pool.get('account.invoice')
                Patient = Pool().get('gnuhealth.patient')
                Details = pool.get("results.details")

                domain = [('create_date', '>=', parameter.start_date), ('create_date', '<=', parameter.end_date), ('invoice.state', '=', 'paid')]

                if parameter.subcategory:
                    domain.append(('product.template.account_category', '=', parameter.subcategory))
                if parameter.category:
                    domain.append(('product.template.account_category', '=', parameter.category))

                invoices_lines = InvoiceLine.search(domain)
                print("invoice lines -- ", parameter.category)

                if not invoices_lines:
                    return []

                result = {}
                Result = []

                for line in invoices_lines:
                    patient_name = line.invoice.party.name or ''
                    patient_lastname = line.invoice.party.lastname or ''
                    if patient_name and patient_lastname:
                        patient = f"{patient_name} {patient_lastname}"
                    else:
                        patient = patient_name or patient_lastname

                    if parameter.subcategory == None:
                        category = parameter.category
                    elif parameter.category == None:
                        category = parameter.subcategory
                    else :
                        category = parameter.subcategory

                    product = line.product.template.name
                    facture = line.invoice.number

                    result = {
                        "patient" : patient,
                        "product" : product,
                        "category" : category.name,
                        "facture" : facture,
                    }

                    Result.append(result)

                    Details.create(Result)


            if parameter.by_prescriptor :
                Results = pool.get("prescriptors.patients")
                Requests = pool.get("account.invoice")
                Details = pool.get("results.details")
                Health_service = pool.get("gnuhealth.health_service")

                invoices = Requests.search([('create_date', '>=', parameter.start_date), ('create_date', '<=', parameter.end_date), ('state', '=', 'paid')])
                list_element_prescriptor = []
                list_of_patient = []
                dict_of_prescriptor = {}
                # exemple de liste des prescripteurs
                # "prod" : [["toto", "tata", "tikol", "fred"], 15]
                for invoice in invoices :
                    element_of_details = []
                    dict_of_detail = {}
                    health_line = Health_service.search([('name', '=', invoice.reference)])
                    for line in health_line:
                        if line.patient.name.name != None and line.patient.name.lastname != None :
                            patient = line.patient.name.name+" "+line.patient.name.lastname
                        if line.patient.name.name == None :
                            patient = line.patient.name.lastname
                        if line.patient.name.lastname == None :
                            patient = line.patient.name.name
                        if line.requestor.name.name != None and line.requestor.name.lastname != None :
                            prescriptor = line.requestor.name.name+" "+line.requestor.name.lastname
                        if line.requestor.name.name == None :
                            prescriptor = line.requestor.name.lastname
                        if line.requestor.name.lastname == None :
                            prescriptor = line.requestor.name.name

                        if dict_of_detail == {} :
                            dict_of_detail = {
                                "prescriptor" : prescriptor,
                                "facture" : invoice.number,
                                "patient" : patient,
                            }
                            element_of_details.append(dict_of_detail)

                            Details.create(element_of_details)

                        if dict_of_prescriptor == {}:
                            list_of_patient.append(patient)
                            list_element_prescriptor.append(list_of_patient)
                            list_element_prescriptor.append(len(list_of_patient))
                            dict_of_prescriptor[prescriptor] = list_element_prescriptor
                        else:
                            if prescriptor in dict_of_prescriptor.keys() :
                                #print("le prescriptor ---- ", dict_of_prescriptor)
                                list_element_prescriptor = dict_of_prescriptor[prescriptor]
                                list_of_patient = list_element_prescriptor[0]
                                if patient not in list_of_patient :
                                    list_of_patient.append(patient)
                                    list_element_prescriptor[1] = len(list_of_patient)
                                    dict_of_prescriptor[prescriptor] = list_element_prescriptor
                            else:
                                list_element_prescriptor = []
                                list_of_patient = []
                                list_of_patient.append(patient)
                                list_element_prescriptor.append(list_of_patient)
                                list_element_prescriptor.append(len(list_of_patient))
                                dict_of_prescriptor[prescriptor] = list_element_prescriptor

                results = []
                if dict_of_prescriptor != {} :
                    for key, value in dict_of_prescriptor.items():

                        d = {}

                        if key not in d:
                            d[key] = value[0]

                        result1 = {
                            'prescriptor' : key,
                            'nombre' : value[1],
                            'dict_prescriptor_patient' : d
                        }

                        results.append(result1)

                    Results.create(results)

                    return results


            if parameter.by_date :
                Results = pool.get("products.number.reports")
                Requests = pool.get("account.invoice.line")

                invoice_lines = Requests.search([('create_date', '>=', parameter.start_date), ('create_date', '<=', parameter.end_date),('product.template.name', '=', parameter.product.template.name), ('invoice.state', '=', 'paid')])

                print("longueur des éléments invoice line ", invoice_lines)
                dict_of_product = {}
                list_of_element = []
                dict_of_product[parameter.product.template.name] = list_of_element


                for invoice_line in invoice_lines :
                    print('le détail -------- ', invoice_line.invoice.number," ------------- ", invoice_line.invoice.party.name +" "+invoice_line.invoice.party.lastname, invoice_line.invoice.invoice_date)
                    if dict_of_product[parameter.product.template.name] == [] :
                        list_of_element.append(invoice_line.quantity)
                        list_of_element.append(invoice_line.unit_price)
                        list_of_element.append(float(list_of_element[0])*float(list_of_element[1]))
                        list_of_element.append(invoice_line.invoice.number)
                        list_of_element.append(invoice_line.invoice.party.name +" "+invoice_line.invoice.party.lastname)
                        list_of_element.append(invoice_line.invoice.invoice_date)
                        dict_of_product[parameter.product.template.name] = list_of_element
                    else :
                        dict_of_product[parameter.product.template.name][0] = dict_of_product[parameter.product.template.name][0] + invoice_line.quantity
                        dict_of_product[parameter.product.template.name][2] = float(dict_of_product[parameter.product.template.name][2]) + float(invoice_line.unit_price)

                results = []

                if dict_of_product[parameter.product.template.name] != [] :
                    result1 = {
                        'product' : parameter.product.template.name,
                        'nombre' : dict_of_product[parameter.product.template.name][0],
                        'prix_u' : dict_of_product[parameter.product.template.name][1],
                        'prix_t' : dict_of_product[parameter.product.template.name][2],
                    }

                    results.append(result1)

                    Results.create(results)

                    return results

            if parameter.by_age :
                Results = pool.get("products.age")
                Requests = pool.get("account.invoice.line")

                invoice_lines = Requests.search([('create_date', '>=', parameter.start_date), ('create_date', '<=', parameter.end_date), ('product.description', '=', parameter.product.description), ('invoice.state', '=', 'paid')])

                print("longueur Longueur ", len(invoice_lines))
                dict_of_product_age = {}
                # Format de la liste des éléments
                # [age_moyen, age_minimum, age_maximum]
                list_of_element = []
                for invoice_line in invoice_lines:
                    list_of_age = []
                    inv = Invoice(invoice_line.invoice)
                    if dict_of_product_age == {} :
                        list_of_age.append(UpdateSelection.age(inv.party.dob))
                        dict_of_product_age[invoice_line.product.template.name] = list_of_age
                    else :
                        if invoice_line.product.template.name in dict_of_product_age :
                            dict_of_product_age[invoice_line.product.template.name].append(UpdateSelection.age(inv.party.dob))
                        else :
                            list_of_age.append(UpdateSelection.age(inv.party.dob))
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

                    print('Les résultats ------- ', dict_of_product_age)

                    return results





