import argparse
import requests
import json
import urllib3
from pathlib import Path

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def find_lockfile(lolPaths, debug=False):
    for lolPath in lolPaths:
        lockfile_path = lolPath / "lockfile"
        if lockfile_path.exists():
            if debug:
                print(f"Found lockfile at: {lockfile_path}")
            return lockfile_path
    return None


def get_lockfile(lolPaths, debug=False):
    lockfile_path = find_lockfile(lolPaths, debug)
    if not lockfile_path:
        raise FileNotFoundError("Lockfile does not exist in any of the specified paths.")

    with open(lockfile_path, "r") as f:
        processName, processId, port, password, protocol = f.read().split(":")

    return port, password, protocol


def init_http_session(password):
    session = requests.Session()
    session.auth = requests.auth.HTTPBasicAuth("riot", password)
    session.verify = False
    return session


def get_loot(http_session, host, port, protocol, debug=False):
    resource_playerloot = "/lol-loot/v1/player-loot"
    url = f"{protocol}://{host}:{port}{resource_playerloot}"
    response = http_session.get(url)
    # if debug:
    #     print(f"GET Request URL: {url}")
    #     print(f"GET Response: {response.text}")
    return json.loads(response.text)


def get_stats(loot_list, debug=False):
    total_blue_essences = sum(loot["disenchantValue"] for loot in loot_list)

    # champ shard only
    champ_shards = []

    for loot in loot_list:
        if loot.get("disenchantLootName") == "CURRENCY_champion":
            champ_shards.append(loot["itemDesc"])
            if debug:
                print(champ_shards)

    return total_blue_essences, champ_shards


def disenchant(http_session, loots, host, port, protocol, debug=False):
    error = False

    for lootid, attributes in loots.items():
        if debug:
            print(f"lootid {lootid}, nb: {attributes['count']}")

        if "CHAMPION_RENTAL_" in lootid:
            uri = "/lol-loot/v1/recipes/CHAMPION_RENTAL_disenchant/craft?repeat="
        else:
            uri = "/lol-loot/v1/recipes/CHAMPION_disenchant/craft?repeat="

        url = f"{protocol}://{host}:{port}{uri}{attributes['count']}"
        body = json.dumps([lootid])
        r = http_session.post(url, data=body)

        if r.status_code == 500:
            error = True

        if debug:
            print(f"POST Request URL: {url}")
            print(f"POST Request Body: {body}")
            print(f"POST Response: {r.text}")

    if error:
        print("[!] Error while deleting some shards, some might still be here ...")
    else:
        print("[+] Done!")


def get_champ_lootid(loots, debug=False):
    champloots = {}
    for loot in loots:
        if loot["disenchantLootName"] == "CURRENCY_champion":
            champloots[loot["lootId"]] = {"count": loot["count"]}
            if debug:
                print(champloots)
    return champloots




def run(lolpaths, exclude_list=None, debug=False):
    host = "127.0.0.1"
    port = None
    password = None
    protocol = None

    for lolPath in lolpaths:
        lolPath = Path(lolPath)
        if not lolPath.is_dir():
            if debug:
                print(f"Path do not exist: {lolPath}")
            continue  # Try the next path
        else:
            if debug:
                print(f"Valid lol path: {lolPath}")

        try:
            port, password, protocol = get_lockfile([lolPath], debug)
            break  # Stop at the first successful lockfile found
        except FileNotFoundError:
            continue  # Try the next path

    if not port or not password or not protocol:
        raise FileNotFoundError("Lockfile does not exist in any of the specified paths.")

    http_session = init_http_session(password)
    loots = get_loot(http_session, host, port, protocol, debug) # loots is a json object
    if debug:
        print(json.dumps(loots, indent=4))

    # Filter loot based on your criteria here

    total_blue_essences, champ_shards = get_stats(loots)
    if total_blue_essences == 0:
        print("[-] No champ shard to delete bro, I'm leaving")
        return

    print(f"[*] {len(loots)} loots are owned")
    print(f"[*] {len(champ_shards)} loots are champions shards")
    print(f"[*] You would win {total_blue_essences} blue essences")
    print(f"[*] Deleted champ shards would be: {', '.join(champ_shards)}")

    champ_to_disenchant = get_champ_lootid(loots)
    if debug:
        print(champ_to_disenchant)
    validation = input("[?] Do you confirm the disenchantment of these champ shards? (yes/no): ").strip().lower()

    if validation == "yes":
        disenchant(http_session, champ_to_disenchant, host, port, protocol, debug)
    else:
        print("[X] You chose not to disenchant, bye")


def main():
    parser = argparse.ArgumentParser(description="Disenchant League of Legends champion shards")
    parser.add_argument(
        "-p",
        "--path",
        action="store",
        default=["C:\\Program Files\\League of Legends", "C:\\Jeux\\League of Legends"],
        type=Path,
        nargs='+',
        help="List of possible paths to League of Legends Folder without '\\' at the end",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        action="store",
        default="",
        type=str,
        help="Comma-separated list of champions to exclude (case insensitive)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode to print debug messages",
    )

    args = parser.parse_args()

    lolPaths = args.path
    run(lolPaths, args.exclude.split(",") if args.exclude else [], args.debug)


if __name__ == "__main__":
    main()
