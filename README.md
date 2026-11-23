# ATT Mod Index

The community list of A Township Tale mods used by **Cheetos Mod Manager**, a Tavern launcher addon that lets players and server owners search for, install and update mods in one click.

## Add your mod

1. Put your mod in a **public** GitHub repo.
2. Make a release and attach your `.dll`, or a `.zip` with the `.dll` inside. To install files into `Plugins` or `UserLibs` too, put them in folders with those names inside the zip.
3. [Submit it here](../../issues/new?template=submit-mod.yml), or use **Submit a mod** in Mod Manager.

A bot checks the submission and adds it within a minute or two. If something's wrong, the bot comments on the issue with the reason. Edit the issue and it checks again.

Mod Manager always installs your **latest release**. To ship an update, publish a new release. The list picks it up within an hour.

## Report a mod

If a mod is broken, harmful, or was listed by someone who doesn't own it, [report it](../../issues/new?template=report-mod.yml).

## How it works

- `mods.json` is the list. Mod Manager reads it straight from this repo.
- `.github/workflows/submit.yml` checks new submission issues and adds them (`scripts/submit.py`).
- `.github/workflows/refresh.yml` updates every mod's latest release once an hour (`scripts/refresh.py`).

Listed mods aren't reviewed, so only install mods you trust.

## Setup notes (repo owner)

- Create the labels `submission` and `report`. Issue forms only apply labels that exist.
- In Settings → Actions → General, set workflow permissions to "Read and write".
