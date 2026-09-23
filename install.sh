#!/usr/bin/env bash
# Convert.id — Automated macOS & Linux One-Liner Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/muhmdathalla/convert.id/main/install.sh | bash

set -e

echo ""
echo "   ______                                __     _     __"
echo "  / ____/___  ____ _   _____  _____/ /_   (_)___/ /"
echo " / /   / __ \/ __ \ | / / _ \/ ___/ __/  / / __  / "
echo "/ /___/ /_/ / / / / |/ /  __/ /  / /_   / / /_/ /  "
echo "\____/\____/_/ /_/|___/\___/_/   \__/  /_/\__,_/   "
echo "Convert.id macOS & Linux All-in-One Installer"
echo ""

# 1. Check Python
echo "[1/4] Checking Python runtime..."
if command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PY_BIN="python"
else
    echo "Error: Python 3 is required. Please install python3 first."
    exit 1
fi

# 2. Setup Directories
INSTALL_DIR="$HOME/.convertid"
BIN_DIR="$INSTALL_DIR/bin"
APP_DIR="$INSTALL_DIR/app"

mkdir -p "$BIN_DIR"
mkdir -p "$APP_DIR"

# 3. Clone or Update
echo "[2/4] Fetching Convert.id core system..."
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull --quiet
else
    git clone https://github.com/muhmdathalla/convert.id.git "$APP_DIR" --quiet
fi

# Install dependencies
$PY_BIN -m pip install -e "$APP_DIR" --quiet

# 4. Create launcher symlinks
cat << 'EOF' > "$BIN_DIR/convert"
#!/usr/bin/env bash
python3 -m convert_id.cli "$@"
EOF
chmod +x "$BIN_DIR/convert"
cp "$BIN_DIR/convert" "$BIN_DIR/convert-id"

# 5. Check PATH in shell profiles
echo "[3/4] Configuring environment PATH..."
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "$BIN_DIR" "$SHELL_RC"; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
        echo "      Added $BIN_DIR to $SHELL_RC"
    fi
fi

# 6. Verify
echo "[4/4] Verifying installation..."
$PY_BIN -m convert_id.cli --version

echo ""
echo "========================================================================"
echo " CONVERT.ID INSTALLED SUCCESSFULLY!"
echo "========================================================================"
echo ""
echo " Try running:"
echo "   convert image.jfif png              # Convert any image"
echo "   convert video.mp4 --target-size 24MB # Fit exact budget"
echo "   convert web                         # Open Monochromatic Web Workbench"
echo "   convert doctor                      # Run system diagnostics"
echo ""
