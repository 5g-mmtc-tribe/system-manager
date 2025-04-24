#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

###############################################################################
# 0. Preconditions
###############################################################################
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <nfsroot-v> <device1> <device2> ..."
    exit 1
fi
[[ $EUID -eq 0 ]] || { echo "Error: must be run as root"; exit 1; }

###############################################################################
# 1. Variables
###############################################################################
NFS_ROOT_V="$1";  shift
DEVICE_NAMES=("$@")

NFS_ROOT="/root/$NFS_ROOT_V"
BASE_ROOTFS="$NFS_ROOT/rootfs"
EXPORTS_FILE="/etc/exports"

# Raspberry-Pi-specific unique directories (copied, never symlinked)
UNIQUE_DIRS=("etc" "var" "home" "root" "dev" "proc" "run" "tmp" "mnt" "sys")

is_unique_dir() {
    local dir=$1
    for u in "${UNIQUE_DIRS[@]}"; do
        [[ "$dir" == "$u" ]] && return 0
    done
    return 1
}

###############################################################################
# 2. Per-device rootfs setup
###############################################################################
for DEVICE in "${DEVICE_NAMES[@]}"; do
    DEVICE_DIR="$NFS_ROOT/$DEVICE"
    FINAL_ROOT="$DEVICE_DIR/rootfs"
    SHARED_ROOT="$FINAL_ROOT/rootfs_shared"

    # ------------------------------------------------------------------ #
    # 2.0  Early-exit guard: directory already set up ► just (re)bind
    # ------------------------------------------------------------------ #
    if [[ -d "$FINAL_ROOT" ]]; then
        echo "Device $DEVICE already set up. Skipping overlay creation…"
        if ! mountpoint -q "$SHARED_ROOT"; then
            mount --bind "$BASE_ROOTFS" "$SHARED_ROOT"
            echo "Mounted base root filesystem for $DEVICE."
        else
            echo "Shared root filesystem already mounted for $DEVICE."
        fi
        continue          
    fi

    echo "Setting up root filesystem for $DEVICE…"

    # ------------------------------------------------------------------ #
    # 2.1  Create skeleton and bind-mount shared tree
    # ------------------------------------------------------------------ #
    mkdir -p "$FINAL_ROOT" "$SHARED_ROOT"
    mount --bind "$BASE_ROOTFS" "$SHARED_ROOT"
    echo "Mounted base root filesystem for $DEVICE."

    # ------------------------------------------------------------------ #
    # 2.2  Overlay: copy uniques, link shared
    # ------------------------------------------------------------------ #
    for DIR in "$BASE_ROOTFS"/*; do
        DIR_NAME=$(basename "$DIR")
        [[ -d "$DIR" ]] || continue

        TARGET="$FINAL_ROOT/$DIR_NAME"

        if is_unique_dir "$DIR_NAME"; then
            cp -a "$DIR" "$TARGET"
            echo "Copied unique directory $DIR_NAME for $DEVICE."
        else
            ln -s "rootfs_shared/$DIR_NAME" "$TARGET"
            echo "Linked shared directory $DIR_NAME for $DEVICE."
        fi
    done

    # ------------------------------------------------------------------ #
    # 2.3  /etc/exports entry (once)
    # ------------------------------------------------------------------ #
    EXPORT_LINE="${FINAL_ROOT} *(rw,sync,no_subtree_check,no_root_squash,crossmnt)"
    echo "$EXPORT_LINE" >> "$EXPORTS_FILE"
done

###############################################################################
# 3. Shared rootfs export (once)
###############################################################################
BASE_EXPORT="${BASE_ROOTFS} *(rw,sync,no_subtree_check,no_root_squash,crossmnt)"
grep -Fxq "$BASE_EXPORT" "$EXPORTS_FILE" || echo "$BASE_EXPORT" >> "$EXPORTS_FILE"

###############################################################################
# 4. Activate exports
###############################################################################
exportfs -a
systemctl restart nfs-kernel-server

echo "NFS exports configured:"
cat "$EXPORTS_FILE"
echo
echo "NFS setup completed successfully!"
