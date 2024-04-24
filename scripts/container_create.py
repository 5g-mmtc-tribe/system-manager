import subprocess
import re


class Container:

    def __init__(self, distribution,container_name):
        self.distribution = distribution
        self.container_name = container_name



    def start_container(self, distribution, container_name):
        command = ['lxc', 'launch', distribution, container_name]
        subprocess.run(command, check=True)

    def delete_container(self, container_name):
        command = ['lxc', 'delete', container_name, '--force']
        subprocess.run(command, check=True)

    def list_containers(self):
        #command = ["lxc", "list"]
        command = f"lxc list"
        subprocess.run(command, check=True)


    def get_network_interfaces(self, container_name):
        # Execute the command and capture the output
        command = ["lxc", "exec", container_name, "--", "ip", "a"]
        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout

        #print(result)
        #print(type(result))
        #print(type(output))
        #print(output)
        # Initialize an empty list to store the network interfaces
        network_interfaces = []
        
        # Check if the command was successful
        if result.returncode == 0:
            # Use regex to find the network interface information starting with 'eth'
            #pattern = r"(@if2)"
            #\beth\b
            #pattern = r".*eth.\b"
            #pattern = r".*eth.*"
            pattern = r"\beth\w+@if\d+\b"


            matches = re.findall(pattern, result.stdout) # Correctly apply regex to result.stdout
            #print(f"matches are {matches}")
            
            # Add the network interface information to the list
            for match in matches:
                cleaned_match = re.sub(r'@if\d+', '', match)

                network_interfaces.append(cleaned_match)
        else:
            print("Command failed with error:", result.stderr)

        return network_interfaces[0]
    
    
    
    


def main():
    distribution = 'ubuntu:22.04'
    container_name = 'testcontainers'

    container = Container(distribution, container_name)

    #container.start_container(distribution,container_name)
    #print("container started successfully")
    #container.delete_container(container_name)
    #print("container deleted")
    print(container.get_network_interfaces("demo"))


if __name__=="__main__":
    main()