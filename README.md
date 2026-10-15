# Rusti 2 Skins Resource Pack

CustomNPCs skins/sounds pack for Minecraft 1.21.1 (NeoForge, pack_format 34).
Pack contents live in `pack/` (see `pack/README.md` for how to add skins/sounds).

## Build

```bash
python build.py 1.0.0   # -> dist/...-v1.0.0.zip + unversioned copy, prints sha1
```

## Release (versioned + static link)

```bash
git tag v1.0.1 && git push origin v1.0.1
```

The `release` workflow builds the pack and publishes a GitHub release with two
assets and the sha1 in the release notes:

- Versioned (pinned, never changes): `https://github.com/OWNER/REPO/releases/download/v1.0.1/Rusti_2_Skins_Resource_Pack-v1.0.1.zip`
- Static (always the newest release): `https://github.com/OWNER/REPO/releases/latest/download/Rusti_2_Skins_Resource_Pack.zip`

Use the static link as `resource-pack=` in prod; the sha1 still has to be
updated from the release notes on each new version. For a pinned server use the
versioned link.

## Update prod after a release

```bash
python server_props.py                    # print the lines for the latest release
python server_props.py server.properties  # or patch a copy in place, then upload it
```

Then restart the server. Planned: a workflow step that runs this against prod
(needs FileBrowser URL/credentials as repo secrets), and/or bundling the pack in
the client modpack so joins skip the full resource reload.

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
