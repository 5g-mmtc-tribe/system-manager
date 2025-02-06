#!/bin/bash

# Directories
BASE_ROOTFS="/root/nfsroot/rootfs"   # Shared root filesystem directory
NFS_ROOT="/root/nfsroot"             # Base NFS directory for device-specific root filesystems

# Check if at least one device name is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <device1> <device2> ..."
    exit 1
fi

# Device-specific overlay directories from arguments
DEVICE_NAMES=("$@")

# Directories that should NOT be shared (unique to each device)
UNIQUE_DIRS=("etc" "var" "dev" "proc" "run" "tmp" "root")

# Function to check if a directory is unique
is_unique_dir() {
    local dir=$1
    for unique_dir in "${UNIQUE_DIRS[@]}"; do
        if [[ "$dir" == "$unique_dir" ]]; then
            return 0
        fi
    done
    return 1
}

# Setup root filesystem for each device
for DEVICE in "${DEVICE_NAMES[@]}"; do
    DEVICE_DIR="$NFS_ROOT/$DEVICE/"
    FINAL_ROOT="$DEVICE_DIR/rootfs"
    SHARED_ROOT="$FINAL_ROOT/rootfs_shared"

    echo "Setting up root filesystem for $DEVICE..."

    # Create necessary directories
    mkdir -p "$FINAL_ROOT"
    mkdir -p "$SHARED_ROOT"

    # **Bind mount BASE_ROOTFS to SHARED_ROOT**
    if ! mountpoint -q "$SHARED_ROOT"; then
        mount --bind "$BASE_ROOTFS" "$SHARED_ROOT"
    fi

    # Iterate through directories in BASE_ROOTFS
    for DIR in "$BASE_ROOTFS"/*; do
        DIR_NAME=$(basename "$DIR")

        # Skip if not a directory
        if [ ! -d "$DIR" ]; then
            continue
        fi

        # Handle unique directories
        if is_unique_dir "$DIR_NAME"; then
            # Copy the directory instead of linking
            cp -a "$DIR" "$FINAL_ROOT/$DIR_NAME"
            echo "Copied unique directory $DIR_NAME for $DEVICE."
        else
            # Create a **relative** symbolic link to SHARED_ROOT
            ln -s "rootfs_shared/$DIR_NAME" "$FINAL_ROOT/$DIR_NAME"
            echo "Linked shared directory $DIR_NAME for $DEVICE (relative)."
        fi
    done

    # Customize hostname for each device
    echo "$DEVICE" > "$FINAL_ROOT/etc/hostname"
    echo "Customized hostname for $DEVICE."

done

# Export directories via NFS
EXPORTS_FILE="/etc/exports"
echo "#Configuring NFS exports..." > "$EXPORTS_FILE"

echo "$BASE_ROOTFS *(async,rw,no_root_squash,no_all_squash,no_subtree_check,insecure,anonuid=1000,anongid=1000,crossmnt)" >> "$EXPORTS_FILE"
for DEVICE in "${DEVICE_NAMES[@]}"; do
    FINAL_ROOT="$NFS_ROOT/$DEVICE/rootfs"
    # Add to /etc/exports
    echo "$FINAL_ROOT *(async,rw,no_root_squash,no_all_squash,no_subtree_check,insecure,anonuid=1000,anongid=1000,crossmnt)" >> "$EXPORTS_FILE"   
done

# Restart NFS server
exportfs -a 
echo "Restarting NFS server..."
systemctl restart nfs-kernel-server


# Show final exports
echo "NFS exports configured:"
cat "$EXPORTS_FILE"
