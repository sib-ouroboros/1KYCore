#!/usr/bin/env python3
"""Join current campaign registries into a read-only dependency work list.

Historical dependency inventories may include restored IDs. Only current
registries determine membership; incomplete joins fail rather than omit work.
No database connection or gameplay writes are performed.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build_report():
    folder = ROOT / "docs/audit-data"
    evidence = {}
    def read(name):
        data = (folder / name).read_bytes()
        evidence[name] = hashlib.sha256(data).hexdigest()
        return json.loads(data)
    def index(rows, key):
        result = {row[key]: row for row in rows}
        if len(result) != len(rows):
            raise ValueError("Duplicate " + key)
        return result
    conversations = read("campaign-remaining-conversations-2026-10-05.json")
    models = read("campaign-remaining-models-2026-10-05.json")
    templates = read("campaign-remaining-templates-2026-10-05.json")
    pending = read("campaign-pending-dependencies.json")
    status = read("campaign-restoration-status.json")
    timing = index(read("campaign-conversation-source-timing-review-2026-10-08.json")["rows"], "conversation")
    chains = index(read("campaign-script-chain-inventory-2026-10-08.json")["rows"], "entry")
    details = index(pending["entries"], "entry")
    if set(details) != set(status["pending_entries"]):
        raise ValueError("Pending template registry mismatch")
    groups = {}
    for group, registry, key in [("conversations", conversations, "conversation"), ("templates", templates, "entry"), ("models", models, "entry")]:
        rows = registry["rows"]
        index(rows, key)
        expected = registry.get("count", registry.get("remaining_count"))
        if expected != len(rows):
            raise ValueError("Count mismatch: " + group)
        if group == "templates" and {x[key] for x in rows} != set(details):
            raise ValueError("Template detail membership mismatch")
        result = []
        for row in rows:
            ident = row[key]
            item = {"id": ident, "blockers": row["blockers"], "status": "REVIEW_REQUIRED"}
            if group == "conversations":
                t = timing[ident]
                item["source_timing"] = {k: t[k] for k in ["source_branch", "source_create_last_line_end", "decoded_duration_bounds_valid", "client_line_links_match", "mixed_source_actor_tables"]}
                item["missing_client_references"] = {"UiCamera": row["missing_native_cameras"], "AnimKit": row["missing_native_animkits"]}
                item["packed_fields"] = row["packed_fields"]
                item["next_step"] = ("Obtain matching client camera/animation records" if any(item["missing_client_references"].values()) else "Verify actor semantics, packed packets and exact source/client timing")
            else:
                c = chains[ident]
                item["script_chain"] = {k: c[k] for k in ["own_source_rows", "incoming_rows", "connected_source_rows", "connected_keys", "enum_mismatches"]}
                if group == "templates":
                    item["source_spawns"] = details[ident]["source_spawns"]
                    item["references"] = details[ident]["references"]
                    item["required_review"] = details[ident]["required_review"]
                else:
                    item["missing_client_references"] = row["missing_native_client_references"]
                    item["source_data"] = row["source_data"]
                item["next_step"] = ("Translate connected source AI semantics before importing" if c["enum_mismatches"] else "Validate full dependency and native interaction lifecycle")
            result.append(item)
        groups[group] = {"count": len(result), "blocker_counts_overlap": dict(sorted(Counter(b for x in result for b in x["blockers"]).items())), "rows": sorted(result, key=lambda x: x["id"])}
    return {"basis": "Current pinned release/source registries; not a live server database audit", "counts": {k: v["count"] for k, v in groups.items()}, "pending_spawns": sum(x["source_spawns"] for x in details.values()), "input_sha256": evidence, "groups": groups, "assurance": "Dependency work list only. No camera/condition zeroing, invented timings, model-only completion or NPC AI changes. Missing source joins fail closed."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report()
    data = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(data, encoding="utf8")
        print(json.dumps({"counts": report["counts"], "pending_spawns": report["pending_spawns"]}))
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
