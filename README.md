## Description
Script that allows to disenchant all current owned champions shards.

Composed of 1 python script (disenchantChampShards.py) or the executable version in the dist/ folder.

It can be used as it is after downloading it specifying the Lol folder path, 
or you can move it in your League of Legends game folder to avoid providing the path argument.

## Usage
### Powershell
```powershell
.\dist\disenchantChampShards.exe
```
### Python
```powershell
python disenchantChampShards.py

# If specific path
python disenchantChampShards.py --path 'Y:\\Riot Games\\League of Legends'
```
## Python to exe
```powershell
pyinstaller.exe --onefile .\disenchantChampShards.py
```



