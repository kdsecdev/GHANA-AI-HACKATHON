from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, time, date
from enum import Enum

class OptimizationObjective(str, Enum):
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_COVERAGE = "maximize_coverage"
    MINIMIZE_WAIT_TIME = "minimize_wait_time"
    BALANCE_ALL = "balance_all"

class GTFSRouteType(int, Enum):
    """GTFS route types"""
    TRAM = 0
    SUBWAY = 1
    RAIL = 2
    BUS = 3
    FERRY = 4
    CABLE_TRAM = 5
    AERIAL_LIFT = 6
    FUNICULAR = 7

class GTFSServiceOptimizationRequest(BaseModel):
    """Request model for GTFS service optimization"""
    route_ids: List[str] = Field(..., min_items=1, description="GTFS route_ids to optimize")
    service_ids: List[str] = Field(..., min_items=1, description="GTFS service_ids to consider")
    optimization_date: date = Field(..., description="Date for optimization")
    objective: OptimizationObjective = Field(OptimizationObjective.BALANCE_ALL, description="Optimization objective")
    time_horizon: int = Field(24, ge=1, le=168, description="Time horizon in hours")
    budget_constraint: Optional[float] = Field(None, ge=0, description="Budget constraint")
    
class GTFSStopOptimizationRequest(BaseModel):
    """Request model for stop-based optimization"""
    stop_ids: List[str] = Field(..., min_items=1, description="GTFS stop_ids to optimize")
    service_area_bounds: Dict[str, float] = Field(..., description="Service area bounds (lat/lon)")
    min_stop_spacing: float = Field(200.0, ge=50.0, description="Minimum stop spacing in meters")
    max_walk_distance: float = Field(800.0, ge=100.0, description="Maximum walk distance in meters")
    
    @validator('service_area_bounds')
    def validate_service_area(cls, v):
        required_keys = ['north', 'south', 'east', 'west']
        if not all(key in v for key in required_keys):
            raise ValueError(f'Service area must contain: {required_keys}')
        return v

class GTFSFrequencyOptimizationRequest(BaseModel):
    """Request model for frequency-based optimization using GTFS frequencies.txt concepts"""
    route_id: str = Field(..., description="GTFS route_id")
    trip_id: Optional[str] = Field(None, description="GTFS trip_id (optional)")
    start_time: time = Field(..., description="Service start time")
    end_time: time = Field(..., description="Service end time")
    min_headway: int = Field(300, ge=60, le=3600, description="Minimum headway in seconds")
    max_headway: int = Field(1800, ge=60, le=7200, description="Maximum headway in seconds")
    exact_times: bool = Field(False, description="Whether to use exact times or frequency-based")
    
    @validator('max_headway')
    def validate_headway_range(cls, v, values):
        if 'min_headway' in values and v < values['min_headway']:
            raise ValueError('Max headway must be greater than min headway')
        return v

class GTFSTripOptimizationRequest(BaseModel):
    """Request model for trip optimization"""
    route_id: str = Field(..., description="GTFS route_id")
    service_id: str = Field(..., description="GTFS service_id")
    shape_id: Optional[str] = Field(None, description="GTFS shape_id for route geometry")
    direction_id: Optional[int] = Field(None, ge=0, le=1, description="GTFS direction_id")
    block_id: Optional[str] = Field(None, description="GTFS block_id for vehicle scheduling")
    wheelchair_accessible: Optional[int] = Field(0, ge=0, le=2, description="Wheelchair accessibility")
    bikes_allowed: Optional[int] = Field(0, ge=0, le=2, description="Bikes allowed")

class OptimizedGTFSRoute(BaseModel):
    """Model for an optimized GTFS route"""
    route_id: str
    route_short_name: str
    route_long_name: str
    route_type: GTFSRouteType
    stops: List[Dict[str, Any]]  # Contains stop_id, stop_sequence, arrival_time, departure_time
    shape_id: Optional[str] = None
    estimated_travel_time: float
    expected_demand: float
    cost_estimate: float
    efficiency_score: float
    service_frequency: Dict[str, int]  # headway by time period

class OptimizedGTFSSchedule(BaseModel):
    """Model for an optimized GTFS schedule"""
    route_id: str
    service_id: str
    trips: List[Dict[str, Any]]  # Contains trip_id, departure_time, direction_id, etc.
    frequencies: List[Dict[str, Any]]  # Contains start_time, end_time, headway_secs
    total_vehicles_needed: int
    estimated_cost: float
    service_quality_score: float

class GTFSRouteOptimizationResponse(BaseModel):
    """Response model for GTFS route optimization"""
    optimization_id: str
    objective: OptimizationObjective
    optimized_routes: List[OptimizedGTFSRoute]
    total_cost: float
    coverage_percentage: float
    average_wait_time: float
    optimization_time_ms: float
    recommendations: List[str]
    gtfs_compliance_score: float

class GTFSScheduleOptimizationResponse(BaseModel):
    """Response model for GTFS schedule optimization"""
    optimization_id: str
    route_id: str
    optimized_schedule: OptimizedGTFSSchedule
    performance_metrics: Dict[str, float]
    cost_savings: float
    service_improvement: float
    optimization_time_ms: float
    stop_times_generated: int

class GTFSFleetOptimizationRequest(BaseModel):
    """Request model for fleet optimization using GTFS data"""
    route_ids: List[str] = Field(..., min_items=1, description="GTFS route_ids")
    service_ids: List[str] = Field(..., min_items=1, description="GTFS service_ids")
    depot_stops: List[str] = Field(..., description="Stop IDs serving as depots")
    vehicle_types: List[GTFSRouteType] = Field([GTFSRouteType.BUS], description="Available vehicle types")
    block_constraints: bool = Field(True, description="Whether to enforce block constraints")
    
class GTFSTransferOptimizationRequest(BaseModel):
    """Request model for optimizing transfers using GTFS transfers.txt"""
    from_stop_id: str = Field(..., description="Origin stop_id")
    to_stop_id: str = Field(..., description="Destination stop_id")
    transfer_type: int = Field(0, ge=0, le=3, description="GTFS transfer type")
    min_transfer_time: Optional[int] = Field(None, ge=0, description="Minimum transfer time in seconds")
    max_transfer_time: Optional[int] = Field(None, ge=0, description="Maximum transfer time in seconds")

class GTFSNetworkOptimizationRequest(BaseModel):
    """Request model for network-wide optimization"""
    agency_id: Optional[str] = Field(None, description="GTFS agency_id to optimize")
    route_types: List[GTFSRouteType] = Field([GTFSRouteType.BUS], description="Route types to include")
    service_area_bounds: Dict[str, float] = Field(..., description="Service area bounds")
    optimization_horizon: int = Field(30, ge=1, le=365, description="Optimization horizon in days")
    consider_transfers: bool = Field(True, description="Whether to optimize transfers")
    
class GTFSAccessibilityOptimizationRequest(BaseModel):
    """Request model for accessibility optimization"""
    route_ids: List[str] = Field(..., min_items=1, description="Routes to make accessible")
    wheelchair_accessible_stops: List[str] = Field(..., description="Wheelchair accessible stop_ids")
    target_accessibility_percentage: float = Field(80.0, ge=0.0, le=100.0, description="Target accessibility %")
    
class GTFSCalendarOptimizationRequest(BaseModel):
    """Request model for calendar/service optimization"""
    service_ids: List[str] = Field(..., min_items=1, description="Service IDs to optimize")
    start_date: date = Field(..., description="Service start date")
    end_date: date = Field(..., description="Service end date")
    monday: bool = Field(True)
    tuesday: bool = Field(True)
    wednesday: bool = Field(True)
    thursday: bool = Field(True)
    friday: bool = Field(True)
    saturday: bool = Field(True)
    sunday: bool = Field(True)
    exception_dates: List[date] = Field([], description="Service exception dates")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v