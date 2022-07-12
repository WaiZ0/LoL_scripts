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
    return json.loads(r.text)


def parseLoot(jsonObject) -> dict:
    """
    :param jsonObject: contain all loot as json obj, dict composed of dict of loot
    :return: dict of owned champ available to disenchant and the nb of stack

    Create a dict of champ chard to sell by returning a uniq ID and the nb of stack of this champ
    """
    print(f"[*] {len(jsonObject)} loot found")

    champDict = {}
    cpt = 0
    totalBlueEssences = 0

    # for each loot in the account
    for loot in jsonObject:

        # if loot is champ && champ is owned
        if (
            loot["disenchantLootName"] == "CURRENCY_champion"
            and loot["itemStatus"] == "OWNED"
        ):
            cpt += 1
            totalBlueEssences += loot["value"]

            # Add to dict of: uniq ID + nb of occurrences (stacked champ shards)
            champDict[loot["lootName"]] = loot["count"]

    print(f"[*] {cpt} are champions shards")
    print(f"[*] You would won {totalBlueEssences} blue essences duh")

    if cpt == 0:
        print("[-] No champ shard to delete bro, I'm leaving")
        sys.exit(0)

    return champDict, totalBlueEssences


def disenchant(httpClient, champDict, host, port, protocol):
    """
    :param httpClient:
    :param champDict:
    :param host:
    :param port:
    :param protocol:
    :return:
    """
    print("[+] Disenchanting all owned champions shards ...")
    for lootName, count in champDict.items():
        resource_disenchant = (
            "/lol-loot/v1/recipes/CHAMPION_RENTAL_disenchant/craft?repeat="
        )
        url = f"{protocol}://{host}:{port}{resource_disenchant}{count}"
        body = f'["{lootName}"]'
        r = httpClient.post(url, data=body)
    print("[+] Done !")


def run(riotBaseFolder):
    host = "127.0.0.1"

    # Get context info
    port, password, protocol = get_lockfile(riotBaseFolder)

    # Setup auth
    httpClient = initHttpSession(password)

    # Get list of champ to sell & sell it
    champDict, totalBlueEssences = parseLoot(getLoot(httpClient, host, port, protocol))

    # User confirmation
    validation = query_yes_no(
        "[?] Do you confirm the disenchants of all owned champ shards ?",
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

    args = parser.parse_args()

    lolPath = Path(args.path)
    if lolPath == Path("."):
        print("[*] No path specified, defaulting to current folder")
    else:
        print(f"[*] League of Legend folder path: {lolPath} ")

    # Check if valid directory
    if not lolPath.is_dir():
        print(
            f"[!] Path is not valid, check the League of Legend folder path, also note that valid path does not "
            f"contain '\\' at the end "
        )
        sys.exit(1)

    # run core
    run(lolPath)
