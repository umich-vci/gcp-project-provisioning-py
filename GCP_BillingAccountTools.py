# Import libraries
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
import GCP_iam
import GCP_clients

billingClient = GCP_clients.billing

def createBillingSubaccount(projectId, masterBillingAccount): 
    masterBillingAccount = "billingAccounts/"+masterBillingAccount    
    ## Create Billing Account
    billingAccountBody = {
        "displayName": projectId+"_billing",
        # "open": True,
        "masterBillingAccount": masterBillingAccount
    }
    billingAccountRequest = billingClient.billingAccounts().create(body = billingAccountBody)
    billingAccountResponse = billingAccountRequest.execute()
    print('Creating %s billing subaccount with billingId: %s' %(billingAccountResponse['displayName'], billingAccountResponse['name']))
    return(billingAccountResponse)
    
def setProjectBillingAccount(projectId, billingId):
    billingBody = {
        "billingAccountName":"billingAccounts/"+billingId,
        "billingEnabled": True,
        "projectId": projectId
    }
    billingProjectUpdateRequest = billingClient.projects().updateBillingInfo(name='projects/'+projectId, body = billingBody)
    billingProjectUpdateResponse = billingProjectUpdateRequest.execute()    
    print('Attaching project: %s to billing account: %s' %(projectId, billingId))
    return(billingProjectUpdateResponse)