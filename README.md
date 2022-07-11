## Description
Script that allows to disenchant all current owned champions shards.

Composed of 1 python script (disenchantChampShards.py) or the executable version in the dist/ folder.

It can be used as it is after downloading it, or you can move it in your Riot Games folder to avoid providing the path argument.

## Usage - from powershell
**Note:** Do not put a "\\" at the end of the path like below:

```powershell
PS .\disenchantChampShards.exe --path 'C:\Riot Games\League of Legends'

# or with python
PS python disenchantChampShards.py --path 'C:\Riot Games\League of Legends'
```

If script directly copied into "Riot Games" folder, no path arg needed, examples below:
```powershell
PS cd 'C:\Riot Games\League of Legends'; .\disenchantChampShards.exe'

# or with python
PS cd 'C:\Riot Games\League of Legends'; python disenchantChampShards.py
```



