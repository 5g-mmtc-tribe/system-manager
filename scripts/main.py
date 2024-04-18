import subprocess
from network_interface import NetworkInterface



def main():


    interface_name = "enp2s0"
    #interface_name = "enx3c18a0b38076"
    interface = NetworkInterface(interface_name) # Replace with your interface name
    if interface.check_interface_exists():
        if interface.check_interface_up():
            print(f"Interface {interface.interface_name} exists and is up.")
        else:
            print(f"Interface {interface.interface_name} exists but is not up.")
    else:
        print(f"Interface {interface.interface_name} does not exist.")




if __name__== "__main__":
    main()