from fastapi import FastAPI
from subprocess import run, CalledProcessError
import os
app = FastAPI()

@app.post("/launch_user_env")
async def launch_script():
    try:
        # Construct the path to the scripts directory relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(script_dir, "../scripts")
        
        # Construct the path to main.py
        main_script_path = os.path.join(scripts_dir, "main.py")
        run(["python", main_script_path], check=True)
        return {"message": "User environment configured properly"}
    except CalledProcessError as e:
        return {"error": f"Error launching script: {e}"}



@app.post("/destroy_user_env")
async def launch_script():
    try:
        # Construct the path to the scripts directory relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(script_dir, "../scripts")
        
        # Construct the path to main.py
        destroy_script_path = os.path.join(scripts_dir, "destroy_env.py")
        run(["python", destroy_script_path], check=True)
        return {"message": "User env destroyed successfully"}
    except CalledProcessError as e:
        return {"error": f"Error launching script: {e}"}


