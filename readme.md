To lauch the system manager application type

uvicorn launch:app --reload

To lauch a script you can execute the following command


Creating user environment
curl -X POST http://127.0.0.1:8000/launch_user_env

Destroying user environment
curl -X POST http://127.0.0.1:8000/destroy_user_env

