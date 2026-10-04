"""Export verified ruRU apply packages to native updater directories.

Run with --check to verify the committed files without writing anything.
No database access; rollback packages are deliberately excluded.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def export(root, check=False):
    records = []
    expected = set()
    for bundle, database in (("world", "world"), ("hotfix", "hotfixes")):
        source = root / "sql/optional/ruRU/2026-10-04" / bundle
        destination = root / "sql/updates" / database / "ruRU"
        catalog = json.loads((source / "catalog.json").read_text(encoding="utf-8"))
        for entry in catalog["packages"]:
            name = entry["file"]
            if not name.endswith(".apply.sql.gz"):
                continue
            assert Path(name).name == name
            compressed = (source / name).read_bytes()
            assert hashlib.sha256(compressed).hexdigest() == entry["gzip_sha256"], name
            sql = gzip.decompress(compressed)
            assert len(sql) == entry["sql_bytes"], name
            assert hashlib.sha256(sql).hexdigest() == entry["sql_sha256"], name
            sql.decode("utf-8")
            assert b"\r" not in sql, name
            target = destination / ("zz_2026_10_04_ruRU_" + bundle + "_" + name[:-3])
            expected.add(target)
            if check:
                assert target.read_bytes() == sql, target
            else:
                destination.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    assert target.read_bytes() == sql, target
                else:
                    target.write_bytes(sql)
            records.append({"source": str((source / name).relative_to(root)).replace("\\", "/"),
                            "file": str(target.relative_to(root)).replace("\\", "/"),
                            "bytes": len(sql), "sha256": entry["sql_sha256"],
                            "updater_sha1": hashlib.sha1(sql).hexdigest()})
        for other in destination.rglob("*.sql"):
            assert other in expected, ("Unexpected SQL in localization directory", other)
        # Updater sorts by filename, including historical non-date migrations.
        existing = [p.name for p in (root / "sql/updates" / database).rglob("*.sql")
                    if p not in expected]
        if existing:
            assert max(existing) < min(p.name for p in expected if p.parent == destination)
        attributes = destination / ".gitattributes"
        if check:
            assert attributes.read_bytes() == b"*.sql text eol=lf\n.gitattributes text eol=lf\n"
        else:
            attributes.write_bytes(b"*.sql text eol=lf\n.gitattributes text eol=lf\n")
    manifest = root / "docs/localization/automatic-updates.json"
    data = (json.dumps({"format": 1, "packages": records}, ensure_ascii=False,
                       indent=2) + "\n").encode("utf-8")
    if check:
        assert manifest.read_bytes() == data
    else:
        manifest.write_bytes(data)
    print(f"Verified {len(records)} apply packages, {sum(r['bytes'] for r in records)} SQL bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    export(args.root.resolve(), args.check)
