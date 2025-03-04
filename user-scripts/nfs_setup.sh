#!/bin/bash

# Directories
BASE_ROOTFS="/root/nfsroot/rootfs"   # Shared root filesystem directory
NFS_ROOT="/root/nfsroot"             # Base NFS directory for device-specific root filesystems
EXPORTS_FILE="/etc/exports"

# Directories that should NOT be shared (unique to each device)
UNIQUE_DIRS=("etc" "var" "dev" "proc" "run" "tmp" "root" "mnt" "sys")
# add sys mnt as unique for dycos porpuse 
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

# Ensure at least one device name is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <device1> <device2> ..."
    exit 1
fi

DEVICE_NAMES=("$@")


# Setup root filesystem for each device
for DEVICE in "${DEVICE_NAMES[@]}"; do
    DEVICE_DIR="$NFS_ROOT/$DEVICE"
    FINAL_ROOT="$DEVICE_DIR/rootfs"
    SHARED_ROOT="$FINAL_ROOT/rootfs_shared"

    

    # Skip setup if the device directory already exists
    if [ -d "$FINAL_ROOT" ]; then
        echo "Device $DEVICE already set up. Skipping..."
        if ! mountpoint -q "$SHARED_ROOT"; then
            mount --bind "$BASE_ROOTFS" "$SHARED_ROOT"
            echo "Mounted base root filesystem for $DEVICE."
        else
            echo "Shared root filesystem already mounted for $DEVICE."
        fi

    fi

    echo "Setting up root filesystem for $DEVICE..."

    # Create necessary directories
    mkdir -p "$FINAL_ROOT"
    mkdir -p "$SHARED_ROOT"

    # Bind mount BASE_ROOTFS to SHARED_ROOT (if not already mounted)
    if ! mountpoint -q "$SHARED_ROOT"; then
        mount --bind "$BASE_ROOTFS" "$SHARED_ROOT"
        echo "Mounted base root filesystem for $DEVICE."
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
            # Copy the directory if it doesn't already exist
            if [ ! -d "$FINAL_ROOT/$DIR_NAME" ]; then
                cp -a "$DIR" "$FINAL_ROOT/$DIR_NAME"
                echo "Copied unique directory $DIR_NAME for $DEVICE."
            fi
        else
            # Create a relative symbolic link to SHARED_ROOT if it doesn't already exist
            if [ ! -L "$FINAL_ROOT/$DIR_NAME" ]; then
                ln -s "rootfs_shared/$DIR_NAME" "$FINAL_ROOT/$DIR_NAME"
                echo "Linked shared directory $DIR_NAME for $DEVICE."
            fi
        fi
    done

    # Customize hostname for each device
    echo "$DEVICE" > "$FINAL_ROOT/etc/hostname"
    echo "Customized hostname for $DEVICE."
    # Ensure rc.local exists and is executable
    RC_LOCAL_FILE="$FINAL_ROOT/etc/rc.local"
    
    if [ ! -f "$RC_LOCAL_FILE" ]; then
        
        touch $RC_LOCAL_FILE
        echo "Creating $RC_LOCAL_FILE"
        sleep 1
       chmod +x "$RC_LOCAL_FILE"
    fi

    # Ensure the shebang line is present at the top of rc.local
    if ! grep -q "^#!/bin/bash" "$RC_LOCAL_FILE"; then
        sed -i '1i #!/bin/bash' "$RC_LOCAL_FILE"
    fi

    # Check if the fan control script is already in rc.local
    if ! grep -q "/usr/bin/python3 /home/mmtc/fan_control.py" "$RC_LOCAL_FILE"; then
        echo "Adding fan control script to $RC_LOCAL_FILE"
        # Insert the command to run the Python script in the background
        sed -i -e "\$i /usr/bin/python3 /home/mmtc/fan_control.py &\n" "$RC_LOCAL_FILE"
    else
        echo "Fan control script is already in rc.local."
    fi
done

# Configure NFS exports
echo "# Configuring NFS exports..." > "$EXPORTS_FILE"

echo "$BASE_ROOTFS *(async,rw,no_root_squash,no_all_squash,no_subtree_check,insecure,anonuid=1000,anongid=1000,crossmnt)" >> "$EXPORTS_FILE"

for DEVICE in "${DEVICE_NAMES[@]}"; do
    FINAL_ROOT="$NFS_ROOT/$DEVICE/rootfs"
    echo "$FINAL_ROOT *(async,rw,no_root_squash,no_all_squash,no_subtree_check,insecure,anonuid=1000,anongid=1000,crossmnt)" >> "$EXPORTS_FILE"
done

# Restart NFS server
echo "Restarting NFS server..."
exportfs -a 
systemctl restart nfs-kernel-server

# Show final exports
echo "NFS exports configured:"
cat "$EXPORTS_FILE"

echo "NFS setup completed successfully!"
