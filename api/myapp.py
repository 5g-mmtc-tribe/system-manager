
from fastapi import FastAPI


app = FastAPI()

def printing(coucou: str):
    print(f"We are testing {coucou}")

@app.get("/print_message")
def print_message(coucou: str):
    try:
        # Call the printing function with the provided message
        printing(coucou)
        return {"message": f"We are testing {coucou}"}
    except Exception as e:
        return {"error": f"Error calling printing function: {e}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

