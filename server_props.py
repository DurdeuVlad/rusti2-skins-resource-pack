"""Usage: python server_props.py [server.properties] [--tag vX.Y.Z]
Reads the release's sha1 from GitHub (latest by default) and prints the resource-pack
lines for server.properties. With a file path, patches those keys in place (keeps the
rest untouched) so a deploy step can reuse it later. Restart the server afterwards."""
import json, re, sys, urllib.request
REPO, NAME = "DurdeuVlad/rusti2-skins-resource-pack", "Rusti_2_Skins_Resource_Pack"
ID = "7f3c1c6e-5b0a-4d8e-9a52-3e1d6b8f4a10"  # keep fixed so clients replace, not stack, the pack
args = sys.argv[1:]
tag = args[args.index("--tag") + 1] if "--tag" in args else None
path = next((a for a in args if a != tag and not a.startswith("--")), None)
api = f"https://api.github.com/repos/{REPO}/releases/" + (f"tags/{tag}" if tag else "latest")
rel = json.load(urllib.request.urlopen(api))
sha = re.search(r"resource-pack-sha1=([0-9a-f]{40})", rel["body"]).group(1)
base = f"https://github.com/{REPO}/releases/" + (f"download/{rel['tag_name']}/{NAME}-{rel['tag_name']}.zip" if tag else f"latest/download/{NAME}.zip")
props = {"require-resource-pack": "true", "resource-pack": base, "resource-pack-id": ID,
         "resource-pack-prompt": '{"text":"Rusti 2 NPC skins"}', "resource-pack-sha1": sha}
if not path:
    print("\n".join(f"{k}={v}" for k, v in props.items())); sys.exit()
text = open(path, encoding="utf-8", newline="").read()
for k, v in props.items():
    text, n = re.subn(rf"^{re.escape(k)}=.*$", lambda _: f"{k}={v}", text, flags=re.M)
    if not n: text += ("" if text.endswith("\n") else "\n") + f"{k}={v}\n"
open(path, "w", encoding="utf-8", newline="").write(text)
print(f"patched {path} -> {rel['tag_name']} sha1={sha}")
