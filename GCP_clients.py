from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
import os

def loadServiceAccountFile(filename):    
    jsonFile = filename
    keyFile = os.path.join(os.path.expanduser("~"), jsonFile) #filename in home directory
    return keyFile

def getServiceAccountCredentials(filename): 
    if os.path.isfile(filename):
        keyfile = filename
    else:
        keyFile = loadServiceAccountFile(filename = filename)
    credentials = ServiceAccountCredentials.from_json_keyfile_name(keyFile)
    return credentials

credentials = GoogleCredentials.get_application_default()
billingCredentials = getServiceAccountCredentials(filename = 'vci-billing-account-creator.json')

billing = discovery.build('cloudBilling', 'v1', credentials = billingCredentials)
bigQuery = discovery.build('bigquery', 'v2', credentials = credentials)
compute = discovery.build('compute', 'v1', credentials = credentials)
resourceManagerClient = discovery.build('cloudresourcemanager', 'v1', credentials = credentials)
loggingClient = discovery.build('logging', 'v2', credentials=credentials)
pubSubClient = discovery.build('pubsub', 'v1', credentials=credentials)
serviceManagementClient = discovery.build('servicemanagement', 'v1', credentials = credentials)
