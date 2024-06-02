import subprocess





def create_user_vm(ubuntu_version, vm_name, root_size):
    # Construct the command using an f-string
    command = f"lxc launch ubuntu:{ubuntu_version} {vm_name} --vm --device root,size={root_size}"


    try:
        # Execute the command
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        # Print the output if successful
        print("STDOUT:", result.stdout)
    except subprocess.CalledProcessError as e:
        # Print the error details
        print("Command failed with return code:", e.returncode)
        print("Command output:", e.output)
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)


# Define the parameters
ubuntu_version = "24.04"
vm_name = "testvm"
root_size = "4GiB"

create_user_vm(ubuntu_version, vm_name, root_size)
