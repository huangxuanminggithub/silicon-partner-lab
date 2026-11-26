#!/usr/bin/env bash
# Installs a deterministic VeriPR pre-push git hook into the current repository.
set -euo pipefail

HOOK_PATH="$(git rev-parse --git-dir)/hooks/pre-push"
cat <<'EOF' > "$HOOK_PATH"
#!/usr/bin/env bash
set -euo pipefail
echo "[VeriPR] Running deterministic anti-cheat audit before push..."
python3 -m veripr --fail-on-cheat
EOF

chmod +x "$HOOK_PATH"
echo "Installed VeriPR pre-push hook at: $HOOK_PATH"
