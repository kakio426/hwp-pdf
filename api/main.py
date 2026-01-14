"""FastAPI application for HWP to PDF conversion service"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: start/stop the conversion worker"""
    from worker.processor import worker
    worker.start()
    yield
    worker.stop()


app = FastAPI(
    title="HWP to PDF Converter API",
    description="Convert HWP files to PDF using Hancom Office OLE automation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api", tags=["conversion"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from worker.processor import worker
    return {
        "status": "healthy",
        "worker_running": worker.is_running
    }
