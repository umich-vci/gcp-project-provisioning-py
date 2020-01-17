import GCP_clients
import GCP_vciTools
import vci_networkTools
import re
import json

def getVpc(projectId, name):
    request = GCP_clients.compute.networks().get(project = projectId, network = name)
    response = request.execute()
    return(response)

def createVpc(projectId, name, autoCreateSubnetworks = False, routing = 'global'):
    # create network body
    networkBody = {        
        "name": name,
        "kind": "compute#network",
        "routingConfig": {
            "routingMode": routing.upper()
        },
    "autoCreateSubnetworks": autoCreateSubnetworks
    }
    # Make the vpc create request
    vpcInsertRequest = GCP_clients.compute.networks().insert(project=projectId, body=networkBody)
    vpcInsertResponse = vpcInsertRequest.execute()
    print('Creating network: %s in projectId: %s' % (name, projectId))    
    return(vpcInsertResponse)

def createVpcSubnet(projectId, region, ipNetwork, networkPrefix, vpc, name):
    if re.search("^https://",vpc):
        vpcUrl = vpc
    else:
        vpcObj = getVpc(projectId = projectId, name = vpc)
        vpcUrl = vpcObj['selfLink']
    # Verify Regions
    try:
        GCP_vciTools.verifyRegions(projectId = projectId, regions = [region])
    except ValueError, e:
        # display error message if necessary e.g. print str(e) 
        print str(e)    
    cidr = ipNetwork+'/'+str(networkPrefix)
    gateway = vci_networkTools.getNetworkGateway(network = cidr)
    regionObj = GCP_vciTools.getRegion(projectId = projectId, region = region)
    regionUrl = regionObj['selfLink']
    # cidr = ipNetwork+'/'+str(networkPrefix)
    subnetBody = {
        "kind": "compute#subnetwork",
        "name": name,
        "network": vpcUrl,
        "ipCidrRange": cidr,
        "gatewayAddress": str(gateway),
        "region": regionUrl,
        "privateIpGoogleAccess": True
    }    
    vpcSubnetInsertRequest = GCP_clients.compute.subnetworks().insert(project=projectId, body=subnetBody, region=region)
    vpcSubnetInsertResponse = vpcSubnetInsertRequest.execute()
    print('Creating %s with network: %s and gateway: %s' %(subnetBody['name'], cidr, gateway))    

def createVpcFirewallRule(projectId, vpc, name, protocol, direction, priority, source = [], port = '', tag = ''):    
    if re.search("^https://",vpc):
        vpcUrl = vpc
    else:
        vpcObj = getVpc(projectId = projectId, name = vpc)
        vpcUrl = vpcObj['selfLink']
    # Set rule type (allowed/denied)
    if 'allow' in name:
        ruleType = "allowed"
    if 'deny' in name:
        ruleType = "denied"
    # set rule direction (ingress/egress)
    if direction.lower() == 'egress':
        targetRanges = "destinationRanges"
    if direction.lower() == 'ingress':
        targetRanges = "sourceRanges"
    # create body
    fwBody = {
        "kind":"compute#firewall",
        "name": name,
        "network": vpcUrl,
        "priority": priority,
        targetRanges:
            source,
        ruleType:[
            {
                "IPProtocol":protocol, 
            }
        ],
        "direction": direction
    }
    # if rule applies to tag
    if tag:
        fwBody.update({"targetTags": tag})    
    # if specifying port
    if port:
        fwBody[ruleType][0].update({"ports":[port]})
    fwRuleReq = GCP_clients.compute.firewalls().insert(project=projectId,body=fwBody)
    fwRuleResponse = fwRuleReq.execute()
    print('Creating firewall rule: {}' .format(name))

def createUmVpc(projectId, purpose, ipNetwork, networkPrefix = 24, regions = []):    
    # create VPC Name
    VPCPrefix = 'um'
    networkName = VPCPrefix + '-' + purpose # + VPCSuffix
    # create VPC
    vpcInfo = createVpc(projectId = projectId, name = networkName)        
    # Wait for VPC creation to complete
    networkOpertation = vpcInfo['name']    
    GCP_vciTools.waitForNetworkOperation(project=projectId,operation=networkOpertation)
    # print(vpcInfo)
    # create subnets
    cidr = ipNetwork+'/'+str(networkPrefix)
    subnets = vci_networkTools.getNetworkSubnets(network = cidr, subnetNumber = len(regions))
    for r in regions:
        subnet = str(subnets[regions.index(r)])
        subnetName = networkName + '-' + r
        createVpcSubnet(projectId = projectId, name = subnetName, vpc = vpcInfo['targetLink'], region = r, ipNetwork = subnet.split('/')[0], networkPrefix = subnet.split('/')[1])
    networkObj = {
        "network":networkName,
        "cidr": cidr
    }
    return(networkObj)    

def createUmFirewall(projectId, vpc, customerNetwork, campusNetworksFile, iaNetworksFile, firewallListFile):
    # import Campus Networks from file
    with open(campusNetworksFile) as filehandle:
        campusNetworks = json.load(filehandle)
    with open (firewallListFile, "r") as filehandle:
        firewallRuleList = json.load(filehandle)
    with open (iaNetworksFile) as filehandle:
        iaNetwork = json.load(filehandle)
    # loop rules
    for rule in firewallRuleList:
        ruleName = rule['name']+'-'+ vpc
        if 'port' in rule:
            port = rule['port']
        else:
            port = ''
        if 'tag' in rule:
            tag = rule['tag']
        else:
            tag = ''
        # check if rule contains these values
        checkSource = ['customer_network', 'campus_networks','ia_network']
        if [i for i in rule['source'] if i in checkSource]:        
            if 'customer_network' in rule['source']:
                source = customerNetwork
            if 'campus_networks' in rule['source']:
                source = campusNetworks
            if 'ia_network' in rule['source']:
                source = iaNetwork
        else:
            source = rule['source']
        createVpcFirewallRule(projectId = projectId, vpc = vpc, name = ruleName, protocol = rule['protocol'], port = port, direction = rule['direction'], priority = rule['priority'], source = source, tag = tag)