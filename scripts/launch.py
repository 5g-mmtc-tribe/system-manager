from fastapi import FastAPI
from subprocess import run, CalledProcessError

app = FastAPI()

@app.post("/launch_script")
async def launch_script():
    try:
        run(["python", "main.py"], check=True)
        return {"message": "Script launched successfully"}
    except CalledProcessError as e:
        return {"error": f"Error launching script: {e}"}

