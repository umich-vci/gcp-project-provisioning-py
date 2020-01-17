# GCP Project Provisioning PUBLIC

## To provision a GCP account:

From the command line, run:

`python GCP_provisionAccount_v2.py path/of/new-project.ini`

## .ini file reference:

### project 
Active = (boolean) impacts the state kept in our database; set to False for temporary/test projects  
ExistingProject = (boolean) Set to True if they already have a project  
BillingContact = (string) Needs to be a Google identity. Will be given Billing Account Viewer on subaccount  
BillingId =  (string)(optional) If left blank, script will create a new billing subaccount. If populated, will associate with given billing subaccount. Format: 112358-EF1234-GFE321  
EgressWaiver = (boolean) Unless one of the items in the NOT allowed section (https://cloud.google.com/billing/docs/how-to/egress-waiver), should be set to True  
Division = (string) Set folder (future, will set place project in folder in hierarchy)  
McommunityGroup = Google Group given permission to project  
ProjectId = (string)(optional) If left blank, must supply ProjectName. If existing project set to True, must supply ProjectId  
ProjectName = A new Google Test Project  
Requestor = (string) Must be a Google Identity. Will be given access to the project  
SecurityContact = (string) Email contact in case of security incident  
Shortcode = (string) Internal billing code  

### networking
VPCPrefix = (string) Prepended to VPC purpose/name  
VPCSuffix = (string) Not in use anymore, but will be appended to VPC name  
VPN = (boolean) If set to True, will create VPN VPC (and eventually VPN)  
SupernetCIDR = (string) Network (in CIDR notation) that will be used to provision VPN IP space (in conjunction with Customer DB)  
SupernetExclude = (string) Network (in CIDR notation) Use if excluding a specific network block from the supernet  

### dataType
(this is kept in the customer database)  

SensitiveData = (boolean)  
PHI = (boolean)  
FERPA = (boolean)  
GLBA = (boolean)  
HSR = (boolean)  
SSN = (boolean)  
ACP = (boolean)  
PII = (boolean)  
ITSecInfo = (boolean)  
PCI = (boolean)  
ITAR = (boolean)  
FISMA = (boolean)  

OtherData = (boolean)  
OtherDataInfo = 

### config
itAdminGroup = (string) Must be a Google Group. Given permission to provision account. Provision removed when provisioning is complete.  
masterBillingAccount = (string) Master Billing Account ID. Format: 011358-ACE135-978675  
logDestionationProject = (string) Project Id to hold Pub/Sub logs  
logDestionationTopic = (string) Pub/Sub topic for logs  

### files
firewallListFile = (string; filepath) json file holding firewall config. Refer to firewall_list_template.json  
campusNetworksFile = (string; filepath) txt file holding campus networks (for VPN routing and firewall). Refer to campus_networks_template.txt  
iaNetworksFile = (string; filepath)   txt file holding IA network (for firewall rules - in case of security issue/forensic need). Refer to ia_networks_template.txt 