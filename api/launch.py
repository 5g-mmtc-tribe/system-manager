from fastapi import FastAPI
from subprocess import run, CalledProcessError

app = FastAPI()

@app.post("/launch_user_env")
async def launch_script():
    try:
        run(["python", "main.py"], check=True)
        return {"message": "User environment configured properly"}
    except CalledProcessError as e:
        return {"error": f"Error launching script: {e}"}



@app.post("/destroy_user_env")
async def launch_script():
    try:
        run(["python", "destroy_env.py"], check=True)
        return {"message": "User env destroyed successfully"}
    except CalledProcessError as e:
        return {"error": f"Error launching script: {e}"}


