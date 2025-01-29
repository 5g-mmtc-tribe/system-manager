
  #!/bin/bash

  # Directories
  BASE_ROOTFS="/root/nfsroot/rootfs"   # Shared root filesystem directory
  NFS_ROOT="/root/nfsroot"             # Base NFS directory for device-specific root filesystems

  # Device-specific overlay directories
  DEVICE_NAMES=("jetson1" "jetson2")

  # Directories that should NOT be shared (unique to each device)
  #UNIQUE_DIRS=("etc" "var" "root" "boot" "dev" "proc" "sys")
  UNIQUE_DIRS=("etc" "var"  "dev" "proc"  "sys" "run" "tmp" "boot" "usr" "bin" "sbin" "lib" "snap" "root" "home")
  # Function to check if a directory is in the unique list
  is_unique_dir() {
    local dir=$1
    for unique_dir in "${UNIQUE_DIRS[@]}"; do
      if [[ "$dir" == "$unique_dir" ]]; then
        return 0
      fi
    done
    return 1
  }

  # Create directories for device root filesystems
  for DEVICE in "${DEVICE_NAMES[@]}"; do
    DEVICE_DIR="$NFS_ROOT/$DEVICE"
    FINAL_ROOT="$DEVICE_DIR/rootfs"

    echo "Setting up root filesystem for $DEVICE..."

    # Create the root filesystem directory for the device
    mkdir -p "$FINAL_ROOT"

    # Iterate through all directories in the base root filesystem
    for DIR in "$BASE_ROOTFS"/*; do
      DIR_NAME=$(basename "$DIR")

      # Skip if the entry is not a directory
      if [ ! -d "$DIR" ]; then
        continue
      fi

      # Check if the directory is unique
      if is_unique_dir "$DIR_NAME"; then
        # Copy unique directory for the device
        cp -a "$DIR" "$FINAL_ROOT/$DIR_NAME"
        echo "Copied unique directory $DIR_NAME for $DEVICE."
      else
        # Create a symbolic link for shared directory
        ln -s "$DIR" "$FINAL_ROOT/$DIR_NAME"
        echo "Linked shared directory $DIR_NAME for $DEVICE."
      fi
    done

    # Customize hostname for the device
    echo "$DEVICE" > "$FINAL_ROOT/etc/hostname"
    echo "Customized hostname for $DEVICE."

  done

  # Export directories via NFS
  EXPORTS_FILE="/etc/exports"
  echo "#Configuring NFS exports..."

  for DEVICE in "${DEVICE_NAMES[@]}"; do
    FINAL_ROOT="$NFS_ROOT/$DEVICE/rootfs"

    # Add wildcard IP entry to /etc/exports
    echo "$FINAL_ROOT *(async,rw,no_root_squash,no_all_squash,no_subtree_check,insecure,anonuid=1000,anongid=1000)" >> "$EXPORTS_FILE"

  done

  # Restart NFS server
  echo "Restarting NFS server..."
  systemctl restart nfs-server

  # Display exports
  echo "NFS exports configured:"
  cat "$EXPORTS_FILE"
