#!/usr/bin/env python3
"""Persistent Human Partner Action Item Tracker for Silicon Partner Lab (EXP-001)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OPS_DIR = Path(__file__).resolve().parent
DEFAULT_JSON = OPS_DIR / "HUMAN_ACTION_ITEMS.json"
DEFAULT_MD = OPS_DIR / "HUMAN_ACTION_ITEMS.md"
VALID_STATUSES = {"TODO", "IN_PROGRESS", "DONE", "SKIPPED"}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_data(json_path: Path) -> dict[str, Any]:
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(json_path: Path, data: dict[str, Any]) -> None:
    data["updated_at"] = now_iso()
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def render_markdown(data: dict[str, Any]) -> str:
    items = data.get("items", [])
    total = len(items)
    done = sum(1 for i in items if i["status"] == "DONE")
    p0_todo = sum(1 for i in items if i["priority"] == "P0" and i["status"] != "DONE")

    status_icon = {
        "TODO": "⬜ TODO",
        "IN_PROGRESS": "🟡 IN_PROGRESS",
        "DONE": "✅ DONE",
        "SKIPPED": "⏭️ SKIPPED",
    }

    lines = [
        "# 人类合伙人协助事项持久化清单（Human Action Items · EXP-001）",
        "",
        f"- **当前阶段**：{data.get('phase', 'Phase 1')}",
        f"- **最后更新（UTC）**：`{data.get('updated_at', '')}`",
        f"- **总体进度**：已完成 `{done}/{total}` 项 ｜ 剩余 P0 阻塞项：`{p0_todo}` 项",
        "- **总计需要人类垫付资金**：`$0.00`（当前所有 P0/P1/P2 事项均为零成本冷启动）",
        "",
        "## 一览表",
        "",
        "| ID | 优先级 | 状态 | 事项 | 预计耗时 | 资金成本 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for item in items:
        st = status_icon.get(item["status"], item["status"])
        lines.append(
            f"| `{item['id']}` | `{item['priority']}` | {st} | {item['title']} | "
            f"~{item['estimated_minutes']} 分钟 | `${item['cost_usd']}` |"
        )

    lines.extend(["", "---", "", "## 逐条操作指引", ""])

    for item in items:
        st = status_icon.get(item["status"], item["status"])
        lines.extend(
            [
                f"### {item['id']} [{item['priority']}] {item['title']}",
                f"- **状态**：{st} ｜ **分类**：`{item['category']}` ｜ **耗时**：~{item['estimated_minutes']} 分钟 ｜ **资金成本**：`${item['cost_usd']}`",
                f"- **为什么必须人类协助**：{item['why_human_needed']}",
                "- **具体执行步骤**：",
            ]
        )
        for idx, step in enumerate(item["steps"], 1):
            lines.append(f"  {idx}. {step}")
        lines.append(f"- **完成后立即解锁**：{item['unlocks']}")
        if item.get("notes"):
            lines.append(f"- **执行备注**：{item['notes']}")
        lines.append("")

    return "\n".join(lines)


def sync_markdown(json_path: Path, md_path: Path) -> None:
    data = load_data(json_path)
    md_path.write_text(render_markdown(data), encoding="utf-8")


def set_status(
    json_path: Path, md_path: Path, item_id: str, status: str, note: str = ""
) -> dict[str, Any]:
    status = status.upper()
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status {status}; expected one of {sorted(VALID_STATUSES)}")
    data = load_data(json_path)
    for item in data["items"]:
        if item["id"] == item_id:
            item["status"] = status
            if note:
                item["notes"] = note
            save_data(json_path, data)
            sync_markdown(json_path, md_path)
            return item
    raise KeyError(f"Action item {item_id} not found")


def add_item(
    json_path: Path,
    md_path: Path,
    item_id: str,
    priority: str,
    category: str,
    title: str,
    minutes: int,
    cost_usd: str,
    why: str,
    steps: list[str],
    unlocks: str,
) -> dict[str, Any]:
    data = load_data(json_path)
    if any(i["id"] == item_id for i in data["items"]):
        raise ValueError(f"Item ID {item_id} already exists")
    new_item = {
        "id": item_id,
        "priority": priority.upper(),
        "status": "TODO",
        "category": category.upper(),
        "title": title,
        "estimated_minutes": minutes,
        "cost_usd": cost_usd,
        "why_human_needed": why,
        "steps": steps,
        "unlocks": unlocks,
        "notes": "",
    }
    data["items"].append(new_item)
    save_data(json_path, data)
    sync_markdown(json_path, md_path)
    return new_item


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Human Partner Action Checklist CLI")
    p.add_argument("--json", dest="json_path", type=Path, default=DEFAULT_JSON)
    p.add_argument("--md", dest="md_path", type=Path, default=DEFAULT_MD)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("render", help="Render HUMAN_ACTION_ITEMS.md from JSON")
    sub.add_parser("list", help="List all action items")

    p_set = sub.add_parser("set-status", help="Update an action item status")
    p_set.add_argument("--id", required=True)
    p_set.add_argument("--status", required=True)
    p_set.add_argument("--note", default="")

    args = p.parse_args(argv)
    if args.cmd == "render":
        sync_markdown(args.json_path, args.md_path)
        print(f"Rendered {args.md_path}")
    elif args.cmd == "list":
        data = load_data(args.json_path)
        for item in data["items"]:
            print(f"{item['id']} [{item['priority']}] ({item['status']}) {item['title']}")
    elif args.cmd == "set-status":
        updated = set_status(args.json_path, args.md_path, args.id, args.status, args.note)
        print(f"Updated {updated['id']} -> {updated['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
