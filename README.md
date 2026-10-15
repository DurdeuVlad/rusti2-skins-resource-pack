# Rusti 2 Skins Resource Pack

CustomNPCs skins/sounds pack for Minecraft 1.21.1 (NeoForge, pack_format 34).
Pack contents live in `pack/` (see `pack/README.md` for how to add skins/sounds).

## Build

```bash
python build.py   # -> dist/Rusti_2_Skins_Resource_Pack.zip + prints sha1
```

## Deploy to prod

1. Upload `dist/Rusti_2_Skins_Resource_Pack.zip` to a direct-download HTTPS URL
   (GitHub release asset, R2, own web server — not a Drive/Dropbox preview link).
2. In prod `server.properties`:
   ```properties
   resource-pack=https://YOUR-HOST/Rusti_2_Skins_Resource_Pack.zip
   resource-pack-sha1=<sha1 printed by build.py>
   require-resource-pack=true
   resource-pack-prompt={"text":"Rusti 2 NPC skins"}
   ```
3. Restart the server (these properties are read only at startup).

Rebuild and update `resource-pack-sha1` every time `pack/` changes, or clients
will keep a stale cached copy. Skins are client-side: players who decline the
pack see pink/black NPCs.
