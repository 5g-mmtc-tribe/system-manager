from setuptools import setup, find_packages

setup(
    name="system_manager",
    version="0.1.0",
    description="A system management suite for VM and network operations",
    author="debbah Mehdi sofiane",
    author_email="mehdi.debbah@hotmail.fr",
    packages=find_packages(),  # This will find packages in directories with __init__.py files.
    install_requires=[
        "fastapi",
        "pandas",
        "pylxd",
        "redis",
        "uvicorn" ,
        "netmiko",
        "python-dotenv",
        "ansible-pylibssh",
 
    ],

)