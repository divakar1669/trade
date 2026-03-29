#!/usr/bin/env bash
set -e

# ── colours ────────────────────────────────────────────────────────────────
C="\033[1;36m"
G="\033[1;32m"
Y="\033[1;33m"
R="\033[1;31m"
D="\033[2m"
RST="\033[0m"

PROJ="$(cd "$(dirname "$0")" && pwd)"
ENV_DIR="$HOME/.trade"
ENV_FILE="$ENV_DIR/.env"
BASHRC="$HOME/.bashrc"

echo ""
echo -e "${C}  trade setup${RST}"
echo -e "${D}  ──────────────────────────────────────${RST}"
echo ""

# ── 1. Python ──────────────────────────────────────────────────────────────
echo -e "${D}  [1/4] Checking Python…${RST}"
if ! command -v python &>/dev/null && ! command -v python3 &>/dev/null; then
    echo -e "${R}  Python not found. Install Python 3.10+ and re-run.${RST}"
    exit 1
fi

PY=$(command -v python || command -v python3)
PYVER=$("$PY" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${G}  ✓ Python $PYVER found${RST}"

# ── 2. Install dependencies ────────────────────────────────────────────────
echo -e "${D}  [2/4] Installing dependencies…${RST}"
cd "$PROJ"
"$PY" -m pip install -e . -q
echo -e "${G}  ✓ All packages installed${RST}"

# ── 3. Create ~/.trade/.env if missing ─────────────────────────────────
echo -e "${D}  [3/4] Setting up config…${RST}"
mkdir -p "$ENV_DIR/tokens"

if [ ! -f "$ENV_FILE" ]; then
    cp "$PROJ/.env.example" "$ENV_FILE"
    echo -e "${G}  ✓ Created ~/.trade/.env${RST}"
    echo -e "${Y}  → Fill in your credentials: ${ENV_FILE}${RST}"
else
    echo -e "${G}  ✓ ~/.trade/.env already exists${RST}"
fi

# ── 4. Add trade function to ~/.bashrc ────────────────────────────────────
echo -e "${D}  [4/4] Wiring up the 'trade' command…${RST}"

# Remove any old trade block
sed -i '/# >>> trade >>>/,/# <<< trade <<</d' "$BASHRC" 2>/dev/null || true

# Detect winpty (Git Bash on Windows needs it)
if command -v winpty &>/dev/null; then
    LAUNCH="winpty \"\$PY\" -m trade"
else
    LAUNCH="\"\$PY\" -m trade"
fi

cat >> "$BASHRC" << EOF

# >>> trade >>>
function trade() {
    local PY="$PY"
    local PROJ="$PROJ"
    (cd "\$PROJ" && $LAUNCH "\$@")
}
# <<< trade <<<
EOF

echo -e "${G}  ✓ 'trade' command added to ~/.bashrc${RST}"
echo ""
echo -e "${D}  ──────────────────────────────────────${RST}"
echo -e "${G}  Setup complete.${RST}"
echo ""
echo -e "  Run ${C}source ~/.bashrc${RST} then type ${C}trade${RST} to open."
echo ""

# ── auto-launch if already sourced ────────────────────────────────────────
if [ "${1}" = "--launch" ]; then
    source "$BASHRC"
    trade
fi
