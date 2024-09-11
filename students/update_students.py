from trytond.model import ModelSQL, fields, ModelView, Workflow
from datetime import datetime
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateAction, StateTransition, Button
import json
import urllib.parse
import requests
from . import API_Params


class Students(ModelSQL, ModelView) :
    "Model View of Result's students"
    __name__ = 'students'

    nom = fields.Char("Nom", size=None)
    prenom = fields.Char("Prenom", size=None)
    naissance = fields.DateTime("Date de Naissance")
    gender2 = fields.Char("Genre", size=None)
    classe = fields.Char("Classe", size=None)
    annee = fields.Char("Année Scolaire", size=None)
    matricule = fields.Char("Matricule", size=None)
    payment_date = fields.Char("Date de payement", size=None)
    frais_medicaux = fields.Boolean("Frais Médicaux", readonly=True)
    description = fields.Char("Description", size=None)

    @classmethod
    def default_frais_medicaux(cls):
        return True


class UpdateStart(ModelSQL, ModelView) :
    "URL API Parameters & Update Students In database"
    __name__ = 'url.parameters'

    YEAR = fields.Char("Academic Year", required=True, size=None)
    SchoolID = fields.Char("School ID", required=True, size=None)
    ClassID = fields.Char("Class ID", size=None)
    StudentID = fields.Char("Student ID", size=None)
    IncludeValidPayments = fields.Boolean("Include Valid Payments")
    IncludeDraftPayments = fields.Boolean("Include Draft Payments")
    IncludeCancelPayments = fields.Boolean("Include Cancel Payments")
    IncludeReduction = fields.Boolean("Include Reductions")
    Requete = fields.Char("Requête", size=None)


    @classmethod
    def default_IncludeValidPayments(cls) :
        return True
    
    @classmethod
    def default_IncludeDraftPayments(cls) :
        return False
    
    @classmethod
    def default_IncludeCancelPayments(cls) :
        return False
    
    @classmethod
    def default_IncludeReduction(cls) :
        return False

class UploadToParty(Wizard) :
    "Upload Student from Results To Party"
    __name__ = "upload.students.start"

    start_state = "upload_"
    upload_ = StateAction('students.act_upload_students')

    @staticmethod
    def do_upload_(self) :

        print("Le Self ----------- ", Transaction().context.get('active_ids'))
        pool = Pool()
        Party = pool.get('party.party')
        Student = pool.get('students')
        Address = pool.get('party.address')

        partie = []
        for id in Transaction().context.get('active_ids') :
            stud = Student(id)
            partie2 = {
                'name' : stud.nom,
                'lastname' : stud.prenom,
                'dob' : stud.naissance,
                'is_patient' : True,
                'is_person' : True,
                'gender' : stud.gender2.lower(),
                'fed_country' : stud.matricule,
            }
            partie.append(partie2)

        address = []
        for party in partie :
            elt = Party.create([party])
            party_id = elt[0].id
            address_party = {
                'party' : party_id
            }
            Address.create([address_party])
        #Party.create(partie)

        return partie2

class UpdateStartMAJ(Wizard) :
    "Wizard to update easily the students databse"
    __name__ = 'url.parameters.start'

    start_state = 'open_'
    open_ = StateAction('students.act_update_students_verify')

    @staticmethod
    def do_open_(self):

        pool = Pool()
        Request = pool.get('url.parameters')
        Result = pool.get('students')

        base_url = 'https://b2i-aca-api.bitang.net/api/student/v1/PAYMENTS'
        results = []
        requestes = Request.browse(Transaction().context.get('active_ids'))
        for request in requestes:
            params = {
                "YEAR": request.YEAR,
                "SchoolID": request.SchoolID,
                "ClassID": request.ClassID,
                "StudentID": request.StudentID,
                "IncludeValidPayments": str(request.IncludeValidPayments).lower(),
                "IncludeDraftPayments": str(request.IncludeDraftPayments).lower(),
                "IncludeCancelPayments": str(request.IncludeCancelPayments).lower(),
                "IncludeReduction": str(request.IncludeReduction).lower(),
                "ApiKey": API_Params.ApiKey
            }

            response = requests.get(base_url, params=params)

            print("Response --- ", len(response.json()))

            if response.status_code == 200:
                students2 = []
                response_json = response.json()
                for elt in response_json:
                    print("Les différents éléments ------------- ", elt["Payment_Reason_Name"])
                    if elt["Payment_Reason_Name"] == "FRAIS MEDICAUX/MEDICAL FEES" :
                        date_string = elt["Student_Birth_Date"].replace('T', ' ')
                        date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
                        stud = Students.search([('matricule', '=', elt["Student_ID_Academy"])])
                        if stud :
                            print("L'étudiant existe déjà")
                        else :
                            student = {
                                'nom': elt["Student_Last_Name"],
                                'prenom': elt["Student_First_Name"],
                                'naissance' : date,
                                'gender2': elt["Student_Gender"],
                                'classe': elt["Class_Name"],
                                'annee': elt["Year_Name"],
                                'matricule': elt["Student_ID_Academy"],
                                'payment_date': elt["Payment_Date_Add"]
                            }
                            students2.append(student)
                Result.create(students2)
                print("Sauvegarde Complète OK", len(students2))
            else:
                print(f"Erreur: {response.status_code}")

        return results
