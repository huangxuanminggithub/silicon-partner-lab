"""Configuration loader for `.veripr.toml` policy files (stdlib tomllib)."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CustomRule:
    rule: str
    severity: str
    category: str
    pattern: re.Pattern[str]
    detail: str


@dataclass
class SensitivePathRule:
    label: str
    pattern: re.Pattern[str]


@dataclass
class PolicyConfig:
    ignore_patterns: list[str] = field(default_factory=list)
    max_assertion_drop: int = 2
    require_clean_tree: bool = False
    disabled_rules: set[str] = field(default_factory=set)
    custom_rules: list[CustomRule] = field(default_factory=list)
    extra_sensitive_paths: list[SensitivePathRule] = field(default_factory=list)
    default_commands: list[str] = field(default_factory=list)


def load_policy(path: Path | None) -> PolicyConfig:
    if path is None or not path.exists():
        return PolicyConfig()

    with path.open("rb") as f:
        raw: dict[str, Any] = tomllib.load(f)

    veripr_sec = raw.get("veripr", {})
    ignore = list(veripr_sec.get("ignore", []))
    max_drop = int(veripr_sec.get("max_assertion_drop", 2))
    require_clean = bool(veripr_sec.get("require_clean_tree", False))
    disabled = set(veripr_sec.get("disable_rules", []))
    default_cmds = list(veripr_sec.get("commands", []))

    custom_rules: list[CustomRule] = []
    for item in raw.get("rules", []):
        sev = str(item.get("severity", "MEDIUM")).upper()
        if sev not in {"HIGH", "MEDIUM", "INFO"}:
            raise ValueError(f"Invalid rule severity in {path}: {sev}")
        flags = re.IGNORECASE if item.get("ignore_case", False) else 0
        custom_rules.append(
            CustomRule(
                rule=str(item["id"]),
                severity=sev,
                category=str(item.get("category", "CUSTOM_POLICY")),
                pattern=re.compile(str(item["regex"]), flags),
                detail=str(item.get("detail", f"Matched custom policy rule {item['id']}")),
            )
        )

    extra_sensitive: list[SensitivePathRule] = []
    for item in raw.get("sensitive_paths", []):
        extra_sensitive.append(
            SensitivePathRule(
                label=str(item["label"]),
                pattern=re.compile(str(item["regex"]), re.IGNORECASE),
            )
        )

    return PolicyConfig(
        ignore_patterns=ignore,
        max_assertion_drop=max_drop,
        require_clean_tree=require_clean,
        disabled_rules=disabled,
        custom_rules=custom_rules,
        extra_sensitive_paths=extra_sensitive,
        default_commands=default_cmds,
    )
