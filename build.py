"""Usage: python build.py [version]  (e.g. 1.0.0)
Build dist/Rusti_2_Skins_Resource_Pack-v<version>.zip plus an identical unversioned
copy (the static-link asset) from pack/, and print the sha1.
Deterministic (sorted, fixed timestamps) so the sha1 only changes when content does."""
import hashlib, pathlib, shutil, sys, zipfile
root = pathlib.Path(__file__).parent
name = "Rusti_2_Skins_Resource_Pack"
ver = sys.argv[1].lstrip("v") if len(sys.argv) > 1 else "dev"
src, out = root / "pack", root / "dist" / f"{name}-v{ver}.zip"
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(p for p in src.rglob("*") if p.is_file()):
        zi = zipfile.ZipInfo(f.relative_to(src).as_posix(), (2026, 1, 1, 0, 0, 0))
        zi.compress_type, zi.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
        z.writestr(zi, f.read_bytes())
shutil.copyfile(out, out.parent / f"{name}.zip")
print(out, out.stat().st_size, "bytes")
print("resource-pack-sha1=" + hashlib.sha1(out.read_bytes()).hexdigest())
