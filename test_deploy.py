"""Throwaway SFTP server + end-to-end check of deploy_sftp.py. Run: python test_deploy.py
(needs paramiko). Proves: only resource-pack keys change, secrets untouched, backup written,
unknown host key rejected, wrong password rejected."""
import base64, os, socket, tempfile, threading, paramiko
from paramiko import SFTPServer, SFTPServerInterface, SFTPAttributes, SFTPHandle, SFTP_OK, ServerInterface, AUTH_SUCCESSFUL, AUTH_FAILED, OPEN_SUCCEEDED
import deploy_sftp

ROOT = tempfile.mkdtemp()
class H(SFTPHandle):
    def __init__(s, f, flags): super().__init__(flags); s.readfile = s.writefile = f
    def stat(s): return SFTPAttributes.from_stat(os.fstat(s.readfile.fileno()))
class FS(SFTPServerInterface):
    def _p(s, p): return os.path.join(ROOT, p.lstrip("/"))
    def open(s, path, flags, attr):
        m = "wb" if flags & os.O_WRONLY else "rb"
        return H(open(s._p(path), m), flags)
    def stat(s, p): return SFTPAttributes.from_stat(os.stat(s._p(p)), p)
    lstat = stat
    MODE = "posix"  # posix | wings (no posix_rename) | strict (no posix_rename, rename refuses existing target)
    def posix_rename(s, a, b):
        if FS.MODE != "posix": return paramiko.SFTP_OP_UNSUPPORTED
        os.replace(s._p(a), s._p(b)); return SFTP_OK
    def rename(s, a, b):
        if FS.MODE == "strict" and os.path.exists(s._p(b)): return paramiko.SFTP_FAILURE
        os.replace(s._p(a), s._p(b)); return SFTP_OK
    def remove(s, p): os.remove(s._p(p)); return SFTP_OK
    def list_folder(s, p): return [SFTPAttributes.from_stat(os.stat(os.path.join(s._p(p), n)), n) for n in os.listdir(s._p(p))]
CK = paramiko.RSAKey.generate(2048)
class Auth(ServerInterface):
    def check_auth_password(s, u, p): return AUTH_SUCCESSFUL if (u, p) == ("deploy", "pw") else AUTH_FAILED
    def check_auth_publickey(s, u, k): return AUTH_SUCCESSFUL if (u, k) == ("deploy", CK) else AUTH_FAILED
    def get_allowed_auths(s, u): return "password,publickey"
    def check_channel_request(s, k, c): return OPEN_SUCCEEDED

hk = paramiko.RSAKey.generate(2048)
srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(5); PORT = srv.getsockname()[1]
def serve():
    while True:
        try: c, _ = srv.accept()
        except OSError: return
        t = paramiko.Transport(c); t.add_server_key(hk); t.set_subsystem_handler("sftp", SFTPServer, FS)
        t.start_server(server=Auth())
threading.Thread(target=serve, daemon=True).start()

PROPS = "motd=x\nrcon.password=SECRET\nrequire-resource-pack=false\nresource-pack=\nresource-pack-sha1=\nwhite-list=true\n"
open(os.path.join(ROOT, "server.properties"), "w").write(PROPS)
good = dict(SFTP_HOST="127.0.0.1", SFTP_PORT=str(PORT), SFTP_USER="deploy", SFTP_PASSWORD="pw",
            SFTP_PATH="/server.properties", SFTP_HOST_KEY=f"{hk.get_name()} {hk.get_base64()}")
SHA = "a" * 40
import io; buf = io.StringIO(); CK.write_private_key(buf)
keyenv = {k: v for k, v in good.items() if k != "SFTP_PASSWORD"} | {"SFTP_KEY": buf.getvalue()}

assert deploy_sftp.deploy(good, SHA, dry_run=True)
assert open(os.path.join(ROOT, "server.properties")).read() == PROPS, "dry run wrote"
assert deploy_sftp.deploy(good, SHA, "v9.9.9")
out = open(os.path.join(ROOT, "server.properties")).read()
assert f"resource-pack-sha1={SHA}" in out and "download/v9.9.9/" in out and "require-resource-pack=true" in out
assert "rcon.password=SECRET" in out and "motd=x" in out and "white-list=true" in out
assert any(f.startswith("server.properties.bak-") for f in os.listdir(ROOT)) and not os.path.exists(os.path.join(ROOT, "server.properties.tmp"))
assert deploy_sftp.deploy(good, SHA, "v9.9.9") is False  # idempotent
for mode in ("wings", "strict"):  # servers without posix_rename (e.g. Pterodactyl Wings)
    FS.MODE = mode; open(os.path.join(ROOT, "server.properties"), "w").write(PROPS)
    assert deploy_sftp.deploy(good, SHA, mode) and f"download/{mode}/" in open(os.path.join(ROOT, "server.properties")).read(), mode
    assert not os.path.exists(os.path.join(ROOT, "server.properties.tmp"))
FS.MODE = "posix"; assert deploy_sftp.deploy(good, SHA, "v9.9.9")
assert deploy_sftp.deploy(keyenv, SHA, "v9.9.9") is False  # key auth works
def other_key():
    b = io.StringIO(); paramiko.RSAKey.generate(2048).write_private_key(b); return b.getvalue()
for bad, why in [({**good, "SFTP_PASSWORD": "nope"}, "bad password"),
                 ({**good, "SFTP_HOST_KEY": f"{hk.get_name()} {paramiko.RSAKey.generate(2048).get_base64()}"}, "wrong host key"),
                 ({**keyenv, "SFTP_KEY": other_key()}, "wrong key")]:
    try: deploy_sftp.deploy(bad, SHA); raise SystemExit(f"FAIL: accepted {why}")
    except (paramiko.AuthenticationException, paramiko.SSHException): pass
print("ALL OK")

# --- blast-radius proof: canary tree + every SFTP call the client makes -------------------
import hashlib
def snap():
    out = {}
    for d, _, fs in os.walk(ROOT):
        for f in fs:
            p = os.path.join(d, f); out[os.path.relpath(p, ROOT).replace(os.sep, "/")] = hashlib.sha1(open(p, "rb").read()).hexdigest()
    return out
CANARIES = ["world/level.dat", "world/region/r.0.0.mca", "plugins/keep.jar", "logs/latest.log", "server.jar",
            "server.properties.bak-old", "server.properties.tmp.keep", "other.properties", "mods/a/b/c.txt"]
for c in CANARIES:
    os.makedirs(os.path.dirname(os.path.join(ROOT, c)) or ROOT, exist_ok=True)
    open(os.path.join(ROOT, c), "wb").write(os.urandom(64))
ops = []
for name in ("remove", "rmdir", "rename", "posix_rename", "mkdir", "symlink", "chmod", "chown", "truncate", "utime", "unlink", "listdir", "listdir_attr"):
    def spy(self, *a, _n=name, _o=getattr(paramiko.SFTPClient, name), **k): ops.append((_n, a)); return _o(self, *a, **k)
    setattr(paramiko.SFTPClient, name, spy)
_open = paramiko.SFTPClient.open
def spy_open(self, path, mode="r", *a, **k):
    if mode != "r": ops.append(("open-" + mode, (path,)))
    return _open(self, path, mode, *a, **k)
paramiko.SFTPClient.open = spy_open
for mode in ("posix", "wings", "strict"):
    FS.MODE = mode; open(os.path.join(ROOT, "server.properties"), "w").write(PROPS)
    for f in list(os.listdir(ROOT)):
        if f.startswith("server.properties.bak-2"): os.remove(os.path.join(ROOT, f))
    before, ops[:] = snap(), []
    assert deploy_sftp.deploy(good, SHA, f"blast-{mode}")
    after = snap()
    removed = set(before) - set(after); added = set(after) - set(before)
    changed = {k for k in before if k in after and before[k] != after[k]}
    assert not removed - {"server.properties.tmp"}, f"{mode}: deleted {removed}"
    assert changed == {"server.properties"}, f"{mode}: modified {changed}"
    assert len(added) == 1 and next(iter(added)).startswith("server.properties.bak-"), f"{mode}: added {added}"
    assert all(after[c] == before[c] for c in CANARIES), f"{mode}: canary touched"
    allowed = {"/server.properties", "/server.properties.tmp"}
    for op, a in ops:
        assert op in ("open-w", "posix_rename", "rename", "remove"), f"{mode}: unexpected op {op}{a}"
        assert all(p in allowed or p.startswith("/server.properties.bak-") for p in a if isinstance(p, str)), f"{mode}: op outside scope {op}{a}"
        if op == "remove": assert a == ("/server.properties",), f"{mode}: remove target {a}"
    print(f"blast radius [{mode}]: {len(CANARIES)} canaries intact; ops = {[(o, a) for o, a in ops]}")
print("BLAST RADIUS OK")
