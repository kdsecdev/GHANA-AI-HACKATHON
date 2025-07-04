from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
import os
import sys

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from app.endpoints import demand, optimize, health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for loaded models
demand_model = None
route_optimizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models on startup and cleanup on shutdown"""
    global demand_model, route_optimizer
    
    logger.info("Starting up Transport AI Model API...")
    
    # Load demand prediction model
    try:
        import joblib
        demand_model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'demand_model.pkl')
        if os.path.exists(demand_model_path):
            demand_model = joblib.load(demand_model_path)
            logger.info("Demand prediction model loaded successfully")
        else:
            logger.warning("Demand model not found. Run training first.")
    except Exception as e:
        logger.error(f"Error loading demand model: {e}")
    
    # Load route optimizer
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
        from route_optimizer import RouteOptimizer
        route_optimizer = RouteOptimizer()
        logger.info("Route optimizer initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing route optimizer: {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Transport AI Model API...")

# Initialize FastAPI app
app = FastAPI(
    title="Transport AI Model API",
    description="API for transit demand prediction and route optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(demand.router, prefix="/demand", tags=["demand"])
app.include_router(optimize.router, prefix="/optimize", tags=["optimization"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Transport AI Model API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "demand_prediction": "/demand",
            "route_optimization": "/optimize"
        }
    }

# Make models available globally
def get_demand_model():
    return demand_model

def get_route_optimizer():
    return route_optimizer