import sys
import requests
import json
import urllib3
import argparse
from pathlib import Path, WindowsPath

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

"""
Doc
http://www.mingweisamuel.com/lcu-schema/tool/#/Plugin%20lol-loot
"""


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


def get_lockfile(lolPath):
    """
    :param riotBaseFolder: path of riot Folder, may changes

    Get the lockfile info to connect via https.

    Lockfile path example
        Ex: C:\Riot Games\League of Legends\lockfile

    File content struct:
        ProcessName:ProcessId:Port:Password:Protocol
    """

    if lolPath == Path("."):
        # if lockfile is in same dir as script
        lockfilePath = Path.cwd() / "lockfile"

    else:
        # else path is specified from arg
        lockfilePath = lolPath / "lockfile"

    if not lockfilePath.exists():
        print(
            f"[!] lockfile does not exist in this path: {lockfilePath}; please provide a valid path to League of Legend folder"
        )
        sys.exit(1)

    print(f"[*] lockfile file found in {lockfilePath}")
    with open(lockfilePath, "r") as f:
        processName, processId, port, password, protocol = f.read().split(":")
        # print(f'{processName}\n{processId}\n{port}\n{password}\n{protocol}\n')

    return port, password, protocol


def initHttpSession(password):
    """
    :param password:
    :return: http session to use
    """
    s = requests.Session()
    s.auth = requests.auth.HTTPBasicAuth("riot", password)
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
    ressource_playerloot = "/lol-loot/v1/player-loot"
    url = f"{protocol}://{host}:{port}{ressource_playerloot}"
    r = httpClient.get(url)
    # print(json.loads(r.text))
    return json.loads(r.text)


def getStats(jsonObject):
    """
    :param jsonObject:
    :return:

    Return stats from the final json loot obj.
    """
    lootsLen = len(jsonObject)

    lootShardsLen = 0
    totalBlueEssences = 0
    deletedChamp = []

    # for each loot in the account
    for loot in jsonObject:
        totalBlueEssences += loot["disenchantValue"]
        lootShardsLen += 1
        deletedChamp.append(loot["itemDesc"])

    return totalBlueEssences, lootShardsLen, deletedChamp


def genFinalListToSell(jsonObject):
    """
    :param jsonObject: contain all loot as json obj, dict composed of dict of loot
    :return: dict of owned champ available to disenchant and the nb of stack

    Create a dict of champ chard to sell by returning a uniq ID and the nb of stack of this champ
    """

    champDict = {}

    # for each loot in the account
    for loot in jsonObject:
        # Add to dict => champDict[<uniqId>] = <nbOfStackedShards>
        champDict[loot["lootName"]] = loot["count"]

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

    noError = 0
    print("[+] Disenchanting ...")
    for lootName, count in champDict.items():
        resource_disenchant = (
            "/lol-loot/v1/recipes/CHAMPION_RENTAL_disenchant/craft?repeat="
        )
        url = f"{protocol}://{host}:{port}{resource_disenchant}{count}"
        body = f'["{lootName}"]'
        r = httpClient.post(url, data=body)

        if r.status_code == 500:
            noError = 1

    if noError:
        print(f"[!] Error while deleting some shards, some might be still here ...")

    print("[+] Done !")


def onlyOwned(jsonList):
    new_listOfDict = []

    # For each loot in jsonObj
    for loot in jsonList:

        # if owned then keep in list to disenchant, else filtered out
        if loot["itemStatus"] == "OWNED":
            new_listOfDict.append(loot)

    return new_listOfDict


def onlyChamp(jsonList):
    new_listOfDict = []

    # For each loot in jsonObj
    for loot in jsonList:

        # If it is a champ shard
        if loot["disenchantLootName"] == "CURRENCY_champion":
            new_listOfDict.append(loot)

    return new_listOfDict


def champExclude(jsonList, excludeList):
    new_listOfDict = []
    excludeList = [x.lower() for x in excludeList]

    # For each loot in jsonObj
    for loot in jsonList:

        # if the itemDesc value is not in excludeList then append to new list
        if loot["itemDesc"].lower() not in excludeList:

            # then Add to new list
            new_listOfDict.append(loot)

        else:
            # print(f'XX Exluding {loot["itemDesc"]}')
            pass

    return new_listOfDict


def clearExcludeList(jsonList, champList):
    new_champList = []

    # For each loot in jsonObj
    for loot in jsonList:

        # if champ name is in list then add to cleaned list (else bye bye)
        if loot["itemDesc"].lower() in champList:
            new_champList.append(loot["itemDesc"])

    return sorted(new_champList)


def run(riotBaseFolder, excludeList=None):
    host = "127.0.0.1"

    # Get context info
    port, password, protocol = get_lockfile(riotBaseFolder)

    # Setup auth
    httpClient = initHttpSession(password)

    # Get raw list jsonObj from the API
    jsonList = getLoot(httpClient, host, port, protocol)
    print(f"[*] {len(jsonList)} loot found")

    # Only keep champ shard from the json obj
    jsonList = onlyChamp(jsonList)

    # Only keep owned champ shard
    jsonList = onlyOwned(jsonList)

    # Exclude user specified champ from jsonObj if needed
    if excludeList:
        # clean the exclude list of user's error
        excludeList = clearExcludeList(jsonList, excludeList)

        # generate new json loot obj
        jsonList = champExclude(jsonList, excludeList)

        print(
            f'[-] Shard that wont be deleted (and that you get a shard of): {", ".join([x for x in excludeList])}'
        )

    # print(f'{", ".join([loot["itemDesc"] for loot in jsonList])}')

    # Get stat from the json Obj after filter
    totalBlueEssences, lootShardsLen, deletedChamp = getStats(jsonList)
    if totalBlueEssences == 0:
        print("[-] No champ shard to delete bro, I'm leaving")
        sys.exit(0)

    print(f"[*] {len(jsonList)} are owned")
    print(f"[*] {lootShardsLen} are champions shards")
    print(f"[*] You would won {totalBlueEssences} blue essences duh")
    print(f"[*] Deleted shards would be: {', '.join(deletedChamp)}")

    # Generate the final list to disenchant
    champDict = genFinalListToSell(jsonList)

    # User validation
    validation = query_yes_no(
        "[?] Do you confirm the disenchantment of these champ shards ?",
        default="no",
    )

    if not validation:
        print("[X] You choose not to disenchant, bye")
        sys.exit(0)

    # Disenchant shards
    disenchant(httpClient, champDict, host, port, protocol)


if __name__ == "__main__":
    # Handling args
    parser = argparse.ArgumentParser(description="Scripts parameters")
    parser.add_argument(
        "-p",
        "--path",
        action="store",
        default=".\\",
        type=Path,
        help='Path of "League of Legend" Folder without "\\" at the end, default is current folder.\n Ex: '
        "disenchantChampShards.py --path C:\Riot Games\League of Legends",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        action="store",
        default="",
        type=str,
        help="Coma separated list of Champ to exclude(case insensitive), like: --exclude vayne, jinx, trundle,sion,MoRgAnA",
    )

    args = parser.parse_args()

    lolPath = Path(args.path)
    if lolPath == Path("."):
        print("[*] No path specified, defaulting to current folder")
    else:
        print(f"[*] League of Legend folder path: {lolPath} ")

    # handling exclude list if it is not empty
    if args.exclude:

        # deleting space, duplicate, and line return, spliting arg from coma
        excludeList = [champ.strip().lower() for champ in args.exclude.split(",")]
        # print(excludeList)

    else:
        excludeList = []

    # Check if valid directory
    if not lolPath.is_dir():
        print(
            f"[!] Path is not valid, check the League of Legend folder path, also note that valid path does not "
            f"contain '\\' at the end "
        )
        sys.exit(1)

    # run core
    run(lolPath, excludeList)
