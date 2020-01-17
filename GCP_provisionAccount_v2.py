#!/usr/bin/python

# Import libraries
from oauth2client.client import GoogleCredentials
from google.cloud import datastore
from googleapiclient import discovery
import datetime
import sys
import time
import re
import ConfigParser
import GCP_iam
import GCP_BillingAccountTools
import vci_networkTools
import GCP_vciTools
import GCP_clients
import GCP_vciNetworkTools


### ### ## ## # # If creating the project for them, must remove yourself as owner and make the requestor the owner. # ## ## ### ###
### Should check the initial time, then sleep until the half hour? Or do we just let them receive the new GCP notification? ###
if len(sys.argv) > 2 or len(sys.argv) <= 1:
    print "Usage: GCP_Provision_Account /path/to/project.ini"
    exit

new_project_config = ConfigParser.ConfigParser()
new_project_config.readfp(open(sys.argv[1]))
# To test from local file and step through this manually
# new_project_config.readfp(open('/path/to/config_file.ini'))

# config variables

itAdminGroup = new_project_config.get('config', 'itAdminGroup')
masterBillingAccount = new_project_config.get('config','masterBillingAccount')
logDestionationProject = new_project_config.get('config', 'logDestionationProject')
logDestionationTopic = new_project_config.get('config', 'logDestionationTopic')

#datastore info - customer DB
namespace = new_project_config.get('database', 'namespace')
customerDbProject = new_project_config.get('database', 'customerDbProject')
kind = new_project_config.get('database', 'kind')

# project information
active = new_project_config.getboolean('project', 'Active')
billingContact = new_project_config.get('project', 'BillingContact')
billingId = new_project_config.get('project', 'BillingId')
division = new_project_config.get('project', 'Division')
egressWaiver = new_project_config.getboolean('project', 'EgressWaiver')
existingProject = new_project_config.getboolean('project','ExistingProject')
mcomm = new_project_config.get('project', 'McommunityGroup')
projectId = new_project_config.get('project', 'ProjectId')
projectName = new_project_config.get('project','ProjectName')
network = new_project_config.get('networking', 'VPCPrefix') + projectId + new_project_config.get('networking', 'VPCSuffix')
requestor = new_project_config.get('project', 'Requestor')
securityContact = new_project_config.get('project', 'SecurityContact')
shortcode = new_project_config.get('project', 'Shortcode')
defaultCidr = new_project_config.get('networking','DefaultCIDR')
defaultSupernet =  new_project_config.get('networking','DefaultSupernet')
vpn = new_project_config.getboolean('networking', 'VPN')
supernetCidr = new_project_config.get('networking', 'SupernetCIDR')
supernetExclude = new_project_config.get('networking', 'SupernetExclude')

# data security or compliance information
sensitiveData = new_project_config.getboolean('dataType', 'SensitiveData')
phi = new_project_config.getboolean('dataType', 'PHI')
ferpa = new_project_config.getboolean('dataType', 'FERPA')
glba = new_project_config.getboolean('dataType', 'GLBA')
hsr = new_project_config.getboolean('dataType', 'HSR')
ssn = new_project_config.getboolean('dataType', 'SSN')
acp = new_project_config.getboolean('dataType', 'ACP')
pii = new_project_config.getboolean('dataType', 'PII')
itSecInfo = new_project_config.getboolean('dataType', 'ITSecInfo')
itar = new_project_config.getboolean('dataType', 'ITAR')
pci  = new_project_config.getboolean('dataType', 'PCI')
fisma = new_project_config.getboolean('dataType', 'FISMA')
otherData = new_project_config.getboolean('dataType', 'OtherData')
otherDataInfo = new_project_config.get('dataType', 'OtherDataInfo')

# files needed for network/firewall
firewallListFile = new_project_config.get('files', 'firewallListFile')
campusNetworksFile = new_project_config.get('files', 'campusNetworksFile')
iaNetworksFile = new_project_config.get('files', 'iaNetworksFile')

# define credentials to use
credentials = GCP_clients.credentials # We'll need to change this. Google appears to be moving to only allowing API calls from Service Accounts (hence the changes to billing)

# Create Project if needed
if projectId is '' and existingProject is False and projectName is not '': 
    print('Customer did not supply existing projectId. Creating projectId from projectName')   
    projectId = GCP_vciTools.createProjectId(projectName = projectName)
    projectCreate = GCP_vciTools.createProject(projectId = projectId, projectName = projectName)
    GCP_vciTools.waitForResourceOperation(operation = projectCreate['name'])
    # Need to set the Network Name since we did not have a project ID Above
    network = new_project_config.get('networking', 'VPCPrefix') + projectId + new_project_config.get('networking', 'VPCSuffix')    

# PROVISION ACCOUNT

## Give owner permissions to VCI group to perform provisioning steps
tempPermissionsEntity = itAdminGroup
tempPermissionsRole = 'owner'
GCP_iam.editIamBinding(projectId = projectId, role = tempPermissionsRole,  entity = tempPermissionsEntity, entityIsGroup=True, addPermission=True)

## Logging export config

### Create Logging Export in Remote Project
GCP_vciTools.setLogExport(projectId = projectId, destinationProjectId = logDestionationProject, destinationTopic = logDestionationTopic) 

## Give mcomm group editor permissions on project
#### #### NEED TO FIX - if they give a user for MComm group #### ####
permissionsEntity = mcomm
permissionsRole = 'editor'
GCP_iam.editIamBinding(projectId = projectId, role = permissionsRole, entity = permissionsEntity, entityIsGroup=True, addPermission=True)

## Get project Info

### Get Project Info (used later)
projectInfo = GCP_vciTools.getProjectInfo(projectId = projectId)

## Billing Config - If billing ID is empty, create a billing subaccount, then add project to billing account
if billingId == '':
    createBilling = True
    billingAccountCreate = GCP_BillingAccountTools.createBillingSubaccount(projectId = projectId, masterBillingAccount = masterBillingAccount)
    billingId = billingAccountCreate['name'].split('/')[1]

billingAccountCreate = ""

## Attach project to billing subaccount
GCP_BillingAccountTools.setProjectBillingAccount(projectId = projectId, billingId = billingId)

## Set billing account permissions
billingRole = 'viewer'
GCP_iam.editIamBinding(projectId = projectId, role = billingRole, entity = billingContact, product = 'billing', entityIsGroup = False, addPermission = True)
GCP_iam.editIamBinding(projectId = projectId, role = billingRole, entity = mcomm, product = 'billing', entityIsGroup = True, addPermission = True)

# Label Project
GCP_vciTools.setProjectLabel(projectId = projectId, key = 'shortcode',  value = shortcode)

# Networking
# # Enable compute API
api = 'compute'
GCP_vciTools.enableApi(api = api, projectId = projectId)
# # Create default network (all projects)
defaultRegions = ['us-central1', 'us-east1', 'us-east4', 'us-west1']
defaultIpNetwork = defaultCidr.split('/')[0]
defaultNetworkPrefix = defaultCidr.split('/')[1]
defaultVpc = GCP_vciNetworkTools.createUmVpc(projectId = projectId, purpose = 'default', ipNetwork = defaultIpNetwork, networkPrefix = defaultNetworkPrefix, regions = defaultRegions) 
defaultVpcNetwork = defaultVpc['network']

# Create firewall on default VPC
GCP_vciNetworkTools.createUmFirewall(projectId = projectId, vpc = defaultVpcNetwork, customerNetwork = defaultSupernet, campusNetworksFile = campusNetworksFile, iaNetworksFile = iaNetworksFile, firewallListFile = firewallListFile)

# create a VPN VPC if selected
if vpn: # change this in the file (and here)
    print('provisioning vpn vpc')
    # Find next CIDR from customer DB
    networkPrefix = 24
    customerInfo = GCP_vciTools.getCustomerInfoByKey(project = customerDbProject, namespace = namespace, kind = kind, dbKey = 'active', dbValue = True, filename = 'vci-datastore-access.json', serviceAccount = True)  
    nextCustomerNetwork = str(vci_networkTools.getNextCustomerNetwork(customerDbProject = customerDbProject, namespace = namespace, kind = kind, supernetCidr = supernetCidr, excludeNetwork = supernetExclude, dbKey = 'active', dbValue = True, mask = 24, service = 'GCP'))
    print('Assigning {} to projectId: {}'.format(nextCustomerNetwork, projectId))
    nextNetwork = nextCustomerNetwork.split('/')[0]
    # Provision Network
    regions = ['us-central1', 'us-east1']    
    vpcVar = GCP_vciNetworkTools.createUmVpc(projectId = projectId, purpose = 'vpn', ipNetwork = nextNetwork, networkPrefix = networkPrefix, regions = regions) 
    # create variables to write to customer database
    subnet = vpcVar['cidr']
    network = vpcVar['network']
    # Create firewall for VPN VPC
    GCP_vciNetworkTools.createUmFirewall(projectId = projectId, vpc = network, customerNetwork = nextNetwork, campusNetworksFile = campusNetworksFile, iaNetworksFile = iaNetworksFile, firewallListFile = firewallListFile)
else:
    subnet = ''
    network = ''

# Create Datastore Entity
dateTimeObj = datetime.datetime.utcnow()

## create datastore client
datastoreClient = GCP_iam.dsClient(project = customerDbProject, namespace = namespace, filename = '', serviceAccount = False)
## create datastore task update
task = datastore.Entity(datastoreClient.key('Project'))
task.update({
    'active': active,
    'billingContact': (billingContact.decode('latin1')),
    'billingId': (billingId.decode('latin1')),    
    'dateCreated':(dateTimeObj),    
    #'dateEnded':(dateTimeObj), #When testing - set Active to False, and this to the time it was created
    'egressWaiver': egressWaiver,
    'division': (division.decode('latin1')),
    'mcomm': (mcomm.decode('latin1')),
    'network': (network.decode('latin1')),
    'projectId': (projectId.decode('latin1')),
    'requestor': (requestor.decode('latin1')),
    'securityContact': (securityContact.decode('latin1')),    
    'shortcode': (shortcode.decode('latin1')),
    'subnet': (subnet.decode('latin1')),
    #'subnet': (vpcVar['subnet'].decode('latin1')),
    'vpn': vpn,
    'dt_sensitiveData': sensitiveData,
    'dt_phi': phi,
    'dt_ferpa': ferpa,
    'dt_glba': glba,
    'dt_hsr': hsr,
    'dt_ssn': ssn,
    'dt_acp': acp,
    'dt_pii': pii,
    'dt_itSecInfo': itSecInfo,
    'dt_itar': itar,
    'dt_pci': pci,
    'dt_fisma': fisma,
    'dt_otherData': otherData,
    'dt_otherDataInfo': (otherDataInfo.decode('latin1'))
})

## put the datastore task
datastoreClient.put(task)
print('Writing customer information to customer database')

## Remove Billing Account Admin (if new account created)
if billingAccountCreate !="":
    GCP_iam.editIamBinding(role = 'admin', billingId = billingId, addPermission = False, product = 'billing', removeAll = True)

## Remove owner permissions to VCI group after performing provisioning steps
tempPermissionsEntity = itAdminGroup
tempPermissionsRole = 'owner'
GCP_iam.editIamBinding(projectId = projectId, role = tempPermissionsRole,  entity = tempPermissionsEntity, entityIsGroup=True, addPermission=False)

#if vpn is True:
#    print('Provision the VPN by running the GCP_createVpn.py script and supplying the VPN Key Part (pwsafe), the projectId, and the region (default: us-central1)\nExample:\npython GCP_createVpn.py -p ''kenmoore-test03'' -k ''VpnKeyFromPwsafe!!'' -r ''us-central1''')
