#!/usr/bin/python

# Import libraries
from oauth2client.client import GoogleCredentials
from google.cloud import datastore
from googleapiclient import discovery
import os
import binascii
import ipcalc
import itertools as it
import sys
import time
import re
import math
import ConfigParser
import GCP_iam
import GCP_clients

# define credentials to use
credentials = GoogleCredentials.get_application_default()

# Build Clients
compute = GCP_clients.compute
resourceManagerClient = GCP_clients.resourceManagerClient
loggingClient = GCP_clients.loggingClient
pubSubClient = GCP_clients.pubSubClient
serviceManagementClient = GCP_clients.serviceManagementClient

def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1

def enableApi(projectId, api):
    serviceManagementClient = discovery.build('servicemanagement', 'v1', credentials = credentials)
    serviceBody = {
        "consumerId":"project:"+projectId
    }
    smServicesEnableReq = serviceManagementClient.services().enable(serviceName = api, body = serviceBody)
    smServicesEnableResponse = smServicesEnableReq.execute()
    print('Enabling %s API' %(api))    
    waitForServiceOperation(operation = smServicesEnableResponse['name'])

## Get Info from CustomerDB based on key and value
def getCustomerInfoByKey(project, namespace, kind, dbKey, dbValue, filename = '', serviceAccount = True): 
    # Create Client    
    client = GCP_iam.dsClient(project = project, namespace = namespace, filename = filename, serviceAccount = serviceAccount) 
    # Query Information
    queryKey = dbKey
    queryValue = dbValue
    operator = '='
    # Create Query
    query = client.query(namespace=namespace,kind=kind)
    query.add_filter(queryKey, operator, queryValue)
        # Peform Query
    results=query.fetch()
        # List to hold the data returned
    datastoreList = []
    # Iterate the results
    for item in results:
        datastoreList.append(item)
    return(datastoreList)
        # for item in results:
        #     # print(item)
        #     return(item)

def getCustomerDB(project, namespace, kind, filename = '', serviceAccount = True): 
    # Datastore Information    
    # Create Cloud Datastore Client
    client = GCP_iam.dsClient(project = project, namespace = namespace, filename = filename, serviceAccount = serviceAccount)    
    # Create Query
    query = client.query(namespace=namespace,kind=kind)
    # Peform Query
    results=query.fetch()
    # List to hold the data returned
    datastoreList = []
    # Iterate the results return
    for item in results:
        datastoreList.append(item)
    return(datastoreList)
        
def waitForServiceOperation(operation):
    sys.stdout.write('Waiting for service operation to finish')
    while True:
        smOpsGetReq = serviceManagementClient.operations().get(name = operation)
        smOpsGetResponse = smOpsGetReq.execute()
        if smOpsGetResponse.has_key('done'):
            if smOpsGetResponse['done']:
                print("done.\n")
                return
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(1)

def waitForNetworkOperation(project, operation, region=None):
    sys.stdout.write('Waiting for network operation to finish')        
    while True:
        if region is None:            
            result = compute.globalOperations().get(project=project, operation=operation).execute()
        else:
            result = compute.regionOperations().get(project=project, operation=operation, region=region).execute()
        if result['status'] == 'DONE':
            print("done.\n")
            if 'error' in result:
                raise Exception(result['error'])
            return result
        else:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1)

def waitForResourceOperation(operation):
    sys.stdout.write('Waiting for resource operation to finish')
    while True:
        rmOpsGetReq = resourceManagerClient.operations().get(name = operation)
        rmOpsGetResponse = rmOpsGetReq.execute()
        if rmOpsGetResponse.has_key('done'):
            if rmOpsGetResponse['done']:
                print("done.\n")
                return
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(1)

## Logging export config
def setLogExport(projectId, destinationProjectId, destinationTopic): 
    ### Set Credentials
    credentials = GoogleCredentials.get_application_default()    
    ### Create Logging Export in Remote Project
    logFilterText = "projects/"+projectId+"/logs/cloudaudit.googleapis.com%2Factivity"
    logExportName = projectId +'-log-export'
    pubSubDestination = 'projects/'+destinationProjectId+'/topics/'+destinationTopic 
    logFilter = 'logName='+ '"' + logFilterText + '"'
    ### Create Logging Sink Body
    loggingSinkBody = {    
        "name":logExportName,     
        "destination": 'pubsub.googleapis.com/'+pubSubDestination,    
        "filter": logFilter    
    }    
    ### Create Logging Sink
    loggingSinkCreateReq = loggingClient.projects().sinks().create(parent='projects/'+projectId, uniqueWriterIdentity = True, body=loggingSinkBody)
    loggingSinkCreateResponse = loggingSinkCreateReq.execute()
    print('Creating project log export')
    ### Get IAM policy on pubsub topic
    pubSubTopicIamRequest = pubSubClient.projects().topics().getIamPolicy(resource=pubSubDestination)
    pubSubTopicIamResponse = pubSubTopicIamRequest.execute()
    print('Retrieving pubsub IAM permissions')
    ### Print policy just in case you need it to restore the policy if overwritten
    print(pubSubTopicIamResponse)
    ### Find the index of publisher role so you can append it
    pubSubPublisherIndex = find (lst = pubSubTopicIamResponse['bindings'], key = 'role', value = 'roles/pubsub.publisher')
    ### Append writer to publisher role on remote pub/sub topic
    writerId = loggingSinkCreateResponse['writerIdentity']
    pubSubTopicIamResponse['bindings'][pubSubPublisherIndex]['members'].append(writerId)
    ### Create pubsub IAM Body - setting appended response back
    pubSubSetIamBody = {
        "policy": pubSubTopicIamResponse
    }
    ### Set the policy with the appended publisher
    pubSubSetIamRequest = pubSubClient.projects().topics().setIamPolicy(resource = pubSubDestination, body=pubSubSetIamBody) 
    pubSubSetIamResponse = pubSubSetIamRequest.execute()
    print('Writing pubsub IAM permissions for log export')

def getProjectInfo(projectId):
    projectInfo = GCP_clients.resourceManagerClient.projects().get(projectId = projectId).execute()
    return projectInfo

def setProjectLabel(projectId, key, value):
    projectInfo = getProjectInfo(projectId)
    # Check if project has labels. If not, create dictionary and add it to projectInfo
    if 'labels' not in projectInfo:           
        addDictionary = {key:value}
        projectInfo['labels'] = addDictionary
    # Append the labels dictionary returned. This will be set back in the labels section of the projectLabelBody
    else:
        projectInfo['labels'][key] = value    
    projectLabelBody = {
        "projectId": projectId,
        "parent":{
            "type": projectInfo['parent']['type'],
            "id": projectInfo['parent']['id']
        },
        "labels": projectInfo['labels']#{
            #key: value
        #}
    }
    projectLabelCall = GCP_clients.resourceManagerClient.projects().update(projectId = projectId, body = projectLabelBody).execute()
    print('Assigning label %s:%s on projectId: %s' %(key,value,projectId))
    return projectLabelCall

def createProjectId(projectName):    
    hexStr = binascii.b2a_hex(os.urandom(2))
    # Project ID must be between 6 and 30 characters; only contain lowercase alpha numeric; must being with a letter
    projectId = re.sub('[^0-9a-zA-Z]+', '-', projectName).lower() # +'-'+dateStr    
    notAllowed = ['google']
    if any(word in projectId for word in notAllowed):
        for n in notAllowed:
            if n in projectId:
                projectId = projectId.replace(n,n[0])    
    # to allow for the '-' and random hex (to create unique project ids)
    if len(projectId)>25:
        print('ProjectId: %s is greater than the maximum 25 characters. Truncating and adding random hex now...' %(projectId))
        projectId = (projectId[:25])
    # Add random hex
    projectId = projectId+'-'+hexStr
    return projectId

def createProject(projectId, projectName = None):
    if projectName is None:
        projectName = projectId
    createProjectBody = {
        'projectId' : projectId,        
        'name' : projectName
    }    
    createProjectRequest = GCP_clients.resourceManagerClient.projects().create(body = createProjectBody) 
    createProjectResponse = createProjectRequest.execute()
    print('Creating %s with projectId: %s'%(projectName, projectId))    
    return createProjectResponse
    
def isPower (num, base):    
    if base == 1 and num != 1: return False
    if base == 1 and num == 1: return True
    if base == 0 and num != 1: return False
    power = int (math.log (num, base) + 0.5)
    return base ** power == num

def getRegionList(projectId):
    compute = GCP_clients.compute
    regionRequest = compute.regions().list(project = projectId)
    regionResponse = regionRequest.execute()
    regionList = []
    for item in regionResponse['items']:        
        regionList.append(item['description'])
    return(regionList)

def verifyRegions(projectId, regions = []):
    regionList = getRegionList(projectId = projectId)
    for r in regions:
        if r not in regionList:
            raise ValueError('%s is not a valid GCP region' %(r))

def getRegion(projectId, region):
    request = compute.regions().get(project = projectId, region = region)
    response = request.execute()
    return(response)