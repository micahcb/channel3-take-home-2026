"""Run the FastAPI server. The app is defined in the api package so uvicorn can resolve api:app."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
