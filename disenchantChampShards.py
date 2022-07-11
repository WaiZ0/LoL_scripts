import sys
import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

"""
Doc
http://www.mingweisamuel.com/lcu-schema/tool/#/Plugin%20lol-loot
"""


def get_lockfile(riotBaseFolder):
    """
    :param riotBaseFolder: path of riot Folder, may changes

    Get the lockfile info to connect via https.

    File folder
        D:\Riot Games\League of Legends\lockfile

    File content struct:
        ProcessName:ProcessId:Port:Password:Protocol
    """
    lockfile_path = riotBaseFolder + '\\League of Legends\\lockfile'

    with open(lockfile_path, 'r') as f:
        processName, processId, port, password, protocol = f.read().split(':')
        #print(f'{processName}\n{processId}\n{port}\n{password}\n{protocol}\n')

    return port, password, protocol

def initHttpSession(password):
    """
    :param password:
    :return: http session to use
    """
    s = requests.Session()
    s.auth = requests.auth.HTTPBasicAuth('riot', password)
    s.verify = False
    return s

def getLoot(httpClient, host, port, protocol):
    """
    :param httpClient:
    :param host:
    :param port:
    :param protocol:
    :return: jsonObject of lol client response
    """
    ressource_playerloot = '/lol-loot/v1/player-loot'
    url = f'{protocol}://{host}:{port}{ressource_playerloot}'
    r = httpClient.get(url)
    return json.loads(r.text)


def parseLoot(jsonObject):
    """
    :param jsonObject: contain all loot as json obj, dict composed of dict of loot
    :return: dict of owned champ available to disenchant and the nb of stack

    Create a dict of champ chard to sell by returning a uniq ID and the nb of stack of this champ
    """
    print(f'[*] {len(jsonObject)} loot found')

    champDict = {}
    cpt = 0

    # for each loot in the account
    for loot in jsonObject:

        # if loot is champ && champ is owned
        if loot['disenchantLootName'] == 'CURRENCY_champion' and loot['itemStatus'] == 'OWNED':
            cpt += 1

            # Add to dict of: uniq ID + nb of occurrences (stacked champ shards)
            champDict[loot['lootName']] = loot['count']

    print(f'[*] {cpt} are champions shards')

    if cpt == 0:
        print('[-] No champ shard to delete bro, I\'m leaving')
        sys.exit(0)



    return champDict

def disenchant(httpClient, champDict, host, port, protocol):
    """
    :param httpClient:
    :param champDict:
    :param host:
    :param port:
    :param protocol:
    :return:
    """
    print('[+] Deleting all owned champions shards ...')
    for lootName, count in champDict.items():
        resource_disenchant = '/lol-loot/v1/recipes/CHAMPION_RENTAL_disenchant/craft?repeat='
        url = f'{protocol}://{host}:{port}{resource_disenchant}{count}'
        body = f'[\"{lootName}\"]'
        r = httpClient.post(url, data=body)
    print('[+] Done !')


if __name__ == '__main__':
    # Parameters
    riotBaseFolder = 'E:\\Jeux\\Riot Games'
    host = '127.0.0.1'

    # Get context info
    port, password, protocol = get_lockfile(riotBaseFolder)

    # Setup auth
    httpClient = initHttpSession(password)

    # Get list of champ to sell & sell it
    champDict = parseLoot(getLoot(httpClient, host, port, protocol))
    disenchant(httpClient, champDict, host, port, protocol)



