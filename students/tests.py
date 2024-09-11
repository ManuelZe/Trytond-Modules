import json
import urllib.parse
import requests

# URL de base
base_url = 'https://iuc-api-aca.bitang.net/api/student/v1/PAYMENTS'

params = {
    'Year': '2023-2024',
    'SchoolID': 'IUC',
    'ClassID': 'BTS1 CGE/J B',
    'StudentID': '',
    'IncludeValidPayments': 'true',
    'IncludeDraftPayments': 'false',
    'IncludeCancelledPayments': 'false',
    'IncludeReductions': 'false',
    'ApiKey': 'iucTEST284GUIiji74411zd8zd7878785zdz7'
}

response = requests.get(base_url, params=params)

# Vérification du statut de la réponse
if response.status_code == 200:
    # Parsing de la réponse JSON
    response_json = response.json()
    # Affichage du JSON de manière lisible
    print(type(response_json[0]['Student_Birth_Date']))
    print(json.dumps(response_json[0], indent=4))
else:
    print(f"Erreur: {response.status_code}")
