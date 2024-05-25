from fastapi import FastAPI
from subprocess import run, CalledProcessError
import os
import sys

# Get the absolute path of the parent directory
script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts'))
sys.path.append(script_path)
# Now import the function from the script
from create_env import launch_env
from destroy_env import destroy_user_env
from user_env import UserEnv
from jetson_ctl import Jetson



app = FastAPI()

def create_env(config: UserEnv):
    launch_env(config)
        

def destroy_env(config: UserEnv):
    destroy_user_env(config)


def get_jetsons_list():
    jetson = Jetson()
    print(jetson.list_devices())



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


