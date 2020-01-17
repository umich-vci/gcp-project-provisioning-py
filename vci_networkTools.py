# import 
import GCP_vciTools
import math
import netaddr

def getNextCustomerNetwork(customerDbProject, namespace, kind, supernetCidr, excludeNetwork = '', dbKey = 'active', dbValue = True, mask = 24, service = 'GCP'):
    if service == 'GCP':        
        # customerInfo = GCP_vciTools.getCustomerInfoByKey(project = 'vci-mcloud-service', namespace = 'vci', kind = 'Project', dbKey = 'active', dbValue = True, filename = '', serviceAccount = False)
        customerInfo = GCP_vciTools.getCustomerInfoByKey(project = customerDbProject, namespace = namespace, kind = kind, dbKey = 'active', dbValue = True, filename = '', serviceAccount = False)
        networksInUse = filter(None,([x['subnet'] for x in customerInfo if 'subnet' in x.keys() and x is not None]))
        supersetNetwork = netaddr.IPSet([supernetCidr])
        if excludeNetwork is not '':            
            supersetNetwork.remove(excludeNetwork)
            print(supersetNetwork)
        for i in networksInUse:
            supersetNetwork.remove(i)
        print(supersetNetwork)
    availableIpNetworks = list(supersetNetwork.iter_cidrs())
    nextAvailableIpNetworksList = []
    for ipNetwork in availableIpNetworks:
        if mask >= int(str(ipNetwork).split('/')[1]):
            nextNetworksToUse = list(ipNetwork.subnet(mask))
            nextNetwork = nextNetworksToUse[0]
            break
    return nextNetwork    

def getNetworkSubnets(network, subnetNumber = 2):
    subnetNumberToAdd = math.log(subnetNumber,2)    
    strNetwork = str(network)
    networkMask = int(strNetwork.split('/')[1])
    subnetworkMask = int(networkMask + subnetNumberToAdd)
    networkObj = netaddr.IPNetwork(strNetwork)
    subnets = list(networkObj.subnet(subnetworkMask))
    return subnets

def getNetworkGateway(network):
    ipList = [ip for ip in netaddr.IPNetwork(network)]
    netGw = ipList[1]
    return netGw