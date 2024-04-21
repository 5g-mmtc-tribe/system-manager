import subprocess


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


def main():
    distribution = 'ubuntu:22.04'
    container_name = 'testcontainers'

    container = Container(distribution, container_name)

    container.start_container(distribution,container_name)
    print("container started successfully")
    container.delete_container(container_name)
    print("container deleted")


if __name__=="__main__":
    main()