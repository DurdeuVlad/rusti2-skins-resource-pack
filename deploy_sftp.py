"""Usage: python deploy_sftp.py --sha <sha1> [--tag vX.Y.Z] [--dry-run]
Patch the resource-pack keys of a remote server.properties over SFTP. Does NOT restart
the server. --tag pins the versioned URL (default: static latest link).
Env: SFTP_HOST, SFTP_PORT (22), SFTP_USER, SFTP_PASSWORD or SFTP_KEY (private key text),
SFTP_PATH (remote server.properties), SFTP_HOST_KEY (known_hosts style: "ssh-ed25519 AAAA...";
required - unknown hosts are rejected). Needs: pip install paramiko"""
import argparse, difflib, io, os, sys, time
import paramiko
from server_props import build_props, patch_text

def connect(env):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.RejectPolicy())
    kt, kd = env["SFTP_HOST_KEY"].split()[:2]
    port = int(env.get("SFTP_PORT", 22))
    host = env["SFTP_HOST"] if port == 22 else f"[{env['SFTP_HOST']}]:{port}"
    c.get_host_keys().add(host, kt, paramiko.PKey.from_type_string(kt, __import__("base64").b64decode(kd)))
    key = None
    if env.get("SFTP_KEY"):
        key = paramiko.PKey.from_private_key(io.StringIO(env["SFTP_KEY"]))
    c.connect(env["SFTP_HOST"], port, env["SFTP_USER"], password=env.get("SFTP_PASSWORD"), pkey=key,
              look_for_keys=False, allow_agent=False, timeout=20)
    return c

def deploy(env, sha, tag=None, dry_run=False):
    c = connect(env); sftp = c.open_sftp(); path = env["SFTP_PATH"]
    try:
        old = sftp.open(path).read().decode("utf-8")
        new = patch_text(old, build_props(sha, tag))
        keys = ("resource-pack", "require-resource-pack")  # print only our keys; file holds secrets
        shown = [l for l in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
                 if l[:1] in "+-" and l[1:].startswith(keys)]
        print("\n".join(shown) or "no changes")
        if dry_run or new == old: return old != new
        sftp.open(f"{path}.bak-{time.strftime('%Y%m%d-%H%M%S')}", "w").write(old.encode())
        sftp.open(f"{path}.tmp", "w").write(new.encode())
        sftp.posix_rename(f"{path}.tmp", path)  # atomic swap; no half-written file
        return True
    finally:
        c.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--sha", required=True)
    ap.add_argument("--tag"); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    changed = deploy(os.environ, a.sha, a.tag, a.dry_run)
    print("deployed" if changed and not a.dry_run else "nothing written")
