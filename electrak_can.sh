#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

if [[ -x .venv/bin/python ]]; then
    PYTHON_BIN=.venv/bin/python
else
    PYTHON_BIN=python3
fi

bringup_slcan() {
    local port=${1:-/dev/ttyACM0}
    local iface=${2:-can0}

    echo "$port -> $iface"
    sudo slcand -o -c -s5 "$port" "$iface"
    sudo ip link set "$iface" up
    sudo ip link set "$iface" txqueuelen 1000
}

bringup_vcan() {
    local iface=${1:-vcan0}

    sudo modprobe vcan
    if ! ip link show "$iface" >/dev/null 2>&1; then
        sudo ip link add dev "$iface" type vcan
    fi
    sudo ip link set "$iface" up
}

move() {
    local position=${1:-50}
    local duty=${2:-50}
    local iface=${3:-vcan0}

    "$PYTHON_BIN" python/run.py -l "$position" -s "$duty" -c "$iface"
}

case "${1:-}" in
    slcan)
        bringup_slcan "${2:-/dev/ttyACM0}" "${3:-can0}"
        ;;
    vcan)
        bringup_vcan "${2:-vcan0}"
        ;;
    move)
        shift
        move "$@"
        ;;
    *)
        echo "Usage: $0 {slcan [PORT] [IFACE]|vcan [IFACE]|move [POSITION] [SPEED] [IFACE]}"
        exit 1
        ;;
esac