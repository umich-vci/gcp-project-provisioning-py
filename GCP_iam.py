import os
from google.cloud import storage
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
from google.cloud import datastore
import GCP_clients

def ServiceAccountAuth(filename):    
    jsonFile = filename
    keyFile = os.path.join(os.path.expanduser("~"), jsonFile) #filename in home directory
    return keyFile

def getServiceAccountCredentials(filename): 
    keyFile = ServiceAccountAuth(filename = filename)
    credentials = ServiceAccountCredentials.from_json_keyfile_name(keyFile)
    return credentials


def getAccountListSA(filename): 
    keyFile = ServiceAccountAuth(filename = filename)
    credentials = ServiceAccountCredentials.from_json_keyfile_name(keyFile)
    return credentials

def dsClient(project, namespace, filename = '', serviceAccount = True):
    if serviceAccount is False:
        credentials = GoogleCredentials.get_application_default()
        client = datastore.Client(project = project, namespace = namespace)
    else:
        accountKey = ServiceAccountAuth(filename = filename)
        client = datastore.Client.from_service_account_json(accountKey, project=project,namespace=namespace)
    return client

def storageClient(project, filename = '', serviceAccount = True):
    if serviceAccount is False:
        credentials = GoogleCredentials.get_application_default()
        client = storage.Client(project = project)
    else:
        accountKey = ServiceAccountAuth(filename = filename)
        client = storage.Client.from_service_account_json(accountKey, project=project)
    return client

def find(lst, key, value):
        for i, dic in enumerate(lst):
            if dic[key] == value:
                return i
        return -1

def getIamBinding(projectId,role,product=None):
    if product == None:
        roleText = 'roles/'+role
    else:
        roleText = 'roles/'+product+'.'+role
    get_iam_policy_request_body = {}    
    iamRequest = resourceManagerClient.projects().getIamPolicy(resource=projectId, body=get_iam_policy_request_body)    
    memberList = []
    iamResponse = iamRequest.execute()
    for policy in iamResponse['bindings']:    
        if policy.get('role') == roleText:
            memberList = policy.get('members')
    return(memberList)

def editIamBinding(projectId, role, entity, entityIsGroup=False, addPermission=True, product=None):
    from oauth2client.client import GoogleCredentials
    from googleapiclient import discovery
    # define credentials to use    
    if product is not None:
        role = 'roles/'+product+'.'+role
    else:
        role = 'roles/'+role
    if entityIsGroup is True: 
        entityObj = 'group:'+entity
    if entityIsGroup is False: 
        entityObj = 'user:'+entity           
    # Get current IAM permissions
    if product == 'billing':
        credentials = GCP_clients.billingCredentials        
        billingClient = GCP_clients.billing
        projectBillingInfo = billingClient.projects().getBillingInfo(name = 'projects/'+projectId).execute()        
        billingResource = projectBillingInfo['billingAccountName']
        billingInfo = billingClient.billingAccounts().get(name = billingResource).execute() #['displayName']
        getIamRequest = billingClient.billingAccounts().getIamPolicy(resource = billingResource)        
    else:
        credentials = GCP_clients.credentials
        resourceManagerClient = discovery.build('cloudresourcemanager', 'v1', credentials = credentials)
        getIamRequestBody = {}
        getIamRequest = resourceManagerClient.projects().getIamPolicy(resource = projectId,body = getIamRequestBody)
    getIamResponse = getIamRequest.execute()
    # Find the index of specified role so you can append it        
    roleIndex = find (lst = getIamResponse['bindings'], key = 'role', value = role)
    # If roleIndex == -1, permission doesn't exit, so add new permissions; else edit/append/remove existing
    if roleIndex == -1:
        newBinding = {
            "role": role,
            "members":entityObj
        }
        getIamResponse['bindings'].append(newBinding)    
    # Edit IAM Policy  
    else:        
        if addPermission is True:
            getIamResponse['bindings'][roleIndex]['members'].append(entityObj)            
        #Check if permission is false
        if addPermission is False:
            # Make everything lowercase to compare
            projectIamResponseLowercase = []
            for member in getIamResponse['bindings'][roleIndex]['members']:
                projectIamResponseLowercase.append(member.lower())
            # Find index of user to remove from lowercase list
            removeIndex = projectIamResponseLowercase.index(entityObj.lower())
            removeEntity = getIamResponse['bindings'][roleIndex]['members'][removeIndex]
            # Remove entity from policy
            getIamResponse['bindings'][roleIndex]['members'].remove(removeEntity)        
    # Set IAM Policy back    
    setProjectIamPolicyBody = {
        "policy":getIamResponse
    }
    if product == 'billing':
        setProjectIamPolicyRequest = billingClient.billingAccounts().setIamPolicy(resource = billingResource, body = setProjectIamPolicyBody)
    else:
        setProjectIamPolicyRequest = resourceManagerClient.projects().setIamPolicy(resource = projectId, body = setProjectIamPolicyBody)
    setProjectIamPolicyResponse = setProjectIamPolicyRequest.execute()
    if addPermission == True:
        action = 'Added'
        prep = 'to'
    else:
        action = 'Removed'
        prep = 'from'
    if product == 'billing':                
        print('%s %s %s %s for %s'% (action, role, prep, billingInfo['displayName'], entityObj))        
    else:        
        print('%s %s %s %s for %s'% (action, role, prep, projectId, entityObj)) 



def editIamPermission(projectId, role, entity, entityIsGroup=False, addPermission=True, product=None):    
    # define credentials to use
    credentials = GoogleCredentials.get_application_default()
    if product is not None:
        role = 'roles/'+product+'.'+role
    else:
        role = 'roles/'+role
    if entityIsGroup is True: 
        entityObj = 'group:'+entity
    if entityIsGroup is False: 
        entityObj = 'user:'+entity           
    # Get current IAM permissions
    if product == 'billing':
        billingClient = discovery.build('cloudbilling', 'v1', credentials = credentials)
        projectBillingInfo = billingClient.projects().getBillingInfo(name = 'projects/'+projectId).execute()        
        billingResource = projectBillingInfo['billingAccountName']
        billingInfo = billingClient.billingAccounts().get(name = billingResource).execute() #['displayName']
        getIamRequest = billingClient.billingAccounts().getIamPolicy(resource = billingResource)        
    else:
        resourceManagerClient = discovery.build('cloudresourcemanager', 'v1', credentials = credentials)
        getIamRequestBody = {}
        getIamRequest = resourceManagerClient.projects().getIamPolicy(resource = projectId,body = getIamRequestBody)
    getIamResponse = getIamRequest.execute()
    # Find the index of specified role so you can append it        
    roleIndex = find (lst = getIamResponse['bindings'], key = 'role', value = role)
    # If roleIndex == -1, permission doesn't exit, so add new permissions; else edit/append/remove existing
    if roleIndex == -1:
        newBinding = {
            "role": role,
            "members":entityObj
        }
        getIamResponse['bindings'].append(newBinding)    
    # Edit IAM Policy  
    else:        
        if addPermission is True:
            getIamResponse['bindings'][roleIndex]['members'].append(entityObj)            
        #Check if permission is false
        if addPermission is False:
            # Make everything lowercase to compare
            projectIamResponseLowercase = []
            for member in getIamResponse['bindings'][roleIndex]['members']:
                projectIamResponseLowercase.append(member.lower())
            # Find index of user to remove from lowercase list
            removeIndex = projectIamResponseLowercase.index(entityObj.lower())
            removeEntity = getIamResponse['bindings'][roleIndex]['members'][removeIndex]
            # Remove entity from policy
            getIamResponse['bindings'][roleIndex]['members'].remove(removeEntity)        
    # Set IAM Policy back    
    setProjectIamPolicyBody = {
        "policy":getIamResponse
    }
    if product == 'billing':
        setProjectIamPolicyRequest = billingClient.billingAccounts().setIamPolicy(resource = billingResource, body = setProjectIamPolicyBody)
    else:
        setProjectIamPolicyRequest = resourceManagerClient.projects().setIamPolicy(resource = projectId, body = setProjectIamPolicyBody)
    setProjectIamPolicyResponse = setProjectIamPolicyRequest.execute()
    if addPermission == True:
        action = 'Added'
        prep = 'to'
    else:
        action = 'Removed'
        prep = 'from'
    if product == 'billing':                
        print('%s %s %s %s for %s'% (action, role, prep, billingInfo['displayName'], entityObj))        
    else:        
        print('%s %s %s %s for %s'% (action, role, prep, projectId, entityObj))
