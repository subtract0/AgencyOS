#!/bin/bash
#
# Trinity Local M4 - Simplified Installer
# Works from any directory by detecting script location
#

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
AGENCY_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo "Script location: $SCRIPT_DIR"
echo "Agency root: $AGENCY_ROOT"

# Verify we found the Agency repo
if [[ ! -d "$AGENCY_ROOT/trinity_protocol" ]]; then
    echo "❌ ERROR: Cannot find trinity_protocol at $AGENCY_ROOT/trinity_protocol"
    echo "Please ensure you're running from the Agency repository"
    exit 1
fi

if [[ ! -d "$AGENCY_ROOT/shared" ]]; then
    echo "❌ ERROR: Cannot find shared at $AGENCY_ROOT/shared"
    exit 1
fi

echo "✅ Found Trinity source code at $AGENCY_ROOT"

# Now run the main installer with the correct source directory
export TRINITY_SOURCE_DIR="$AGENCY_ROOT"

# Change to Agency root and run main installer
cd "$AGENCY_ROOT"
exec "$SCRIPT_DIR/install.sh"
