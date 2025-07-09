import uvicorn
import os
from test_mainapp import app

if __name__ == "__main__":
    # Get port from environment variable or default to 8003
    port = int(os.environ.get("PORT", 8003))
    
    # For Linux deployment, bind to 0.0.0.0 to accept external connections
    # For local development, you can use "127.0.0.1" or "localhost"
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Enable reload for development, disable for production
    reload = os.environ.get("RELOAD", "false").lower() == "true"
    
    print(f"Starting server on {host}:{port}")
    print(f"Swagger docs available at: http://{host}:{port}/docs")
    print(f"ReDoc available at: http://{host}:{port}/redoc")
    
    uvicorn.run(
        "test_mainapp:app",
        host=host,
        port=port,
        reload=reload,
        access_log=True
    )