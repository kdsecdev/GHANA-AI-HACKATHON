from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, time, date
from enum import Enum

class DayOfWeek(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class WeatherCondition(str, Enum):
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    SNOWY = "snowy"
    FOGGY = "foggy"

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

class DemandPredictionRequest(BaseModel):
    """Request model for demand prediction using GTFS entities"""
    route_id: str = Field(..., description="GTFS route_id")
    stop_id: str = Field(..., description="GTFS stop_id")
    trip_id: Optional[str] = Field(None, description="GTFS trip_id (optional)")
    service_id: Optional[str] = Field(None, description="GTFS service_id (optional)")
    datetime: datetime = Field(..., description="Prediction datetime")
    direction_id: Optional[int] = Field(None, ge=0, le=1, description="GTFS direction_id (0 or 1)")
    weather_condition: WeatherCondition = Field(WeatherCondition.SUNNY, description="Weather condition")
    temperature: float = Field(20.0, ge=-50, le=60, description="Temperature in Celsius")
    is_holiday: bool = Field(False, description="Whether it's a holiday")
    special_event: Optional[str] = Field(None, description="Special event nearby")
    
    @validator('datetime')
    def validate_datetime(cls, v):
        if v < datetime.now():
            raise ValueError('Prediction datetime must be in the future')
        return v

class GTFSStopInfo(BaseModel):
    """GTFS stop information"""
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    zone_id: Optional[str] = None
    stop_url: Optional[str] = None
    location_type: Optional[int] = Field(0, ge=0, le=4)
    parent_station: Optional[str] = None
    stop_timezone: Optional[str] = None
    wheelchair_boarding: Optional[int] = Field(0, ge=0, le=2)

class GTFSRouteInfo(BaseModel):
    """GTFS route information"""
    route_id: str
    route_short_name: str
    route_long_name: str
    route_type: GTFSRouteType
    route_color: Optional[str] = None
    route_text_color: Optional[str] = None
    agency_id: Optional[str] = None
    route_desc: Optional[str] = None
    route_url: Optional[str] = None

class DemandPredictionBatchRequest(BaseModel):
    """Request model for batch demand prediction"""
    predictions: List[DemandPredictionRequest] = Field(..., min_items=1, max_items=100)

class DemandPredictionResponse(BaseModel):
    """Response model for demand prediction"""
    route_id: str
    stop_id: str
    datetime: datetime
    predicted_demand: float = Field(..., description="Predicted passenger demand")
    confidence_interval: Dict[str, float] = Field(..., description="95% confidence interval")
    factors: Dict[str, Any] = Field(..., description="Key factors influencing prediction")
    route_info: Optional[GTFSRouteInfo] = None
    stop_info: Optional[GTFSStopInfo] = None

class DemandPredictionBatchResponse(BaseModel):
    """Response model for batch demand prediction"""
    predictions: List[DemandPredictionResponse]
    total_predictions: int
    processing_time_ms: float

class GTFSStopTimeAnalysisRequest(BaseModel):
    """Request model for GTFS stop time analysis"""
    route_id: str
    stop_id: str
    service_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    
class GTFSCalendarRequest(BaseModel):
    """Request model using GTFS calendar data"""
    service_id: str
    start_date: date
    end_date: date
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class GTFSTripDemandRequest(BaseModel):
    """Request model for trip-based demand prediction"""
    trip_id: str = Field(..., description="GTFS trip_id")
    service_date: date = Field(..., description="Service date")
    weather_condition: WeatherCondition = Field(WeatherCondition.SUNNY)
    temperature: float = Field(20.0, ge=-50, le=60)
    is_holiday: bool = Field(False)

class GTFSShapeAnalysisRequest(BaseModel):
    """Request model for shape-based analysis"""
    shape_id: str = Field(..., description="GTFS shape_id")
    route_id: Optional[str] = Field(None, description="Filter by route_id")
    
class HistoricalDemandResponse(BaseModel):
    """Response model for historical demand analysis"""
    route_id: str
    stop_id: str
    data: List[Dict[str, Any]]
    statistics: Dict[str, float]
    peak_hours: List[int]
    peak_days: List[str]
    route_info: Optional[GTFSRouteInfo] = None
    stop_info: Optional[GTFSStopInfo] = None

class GTFSFeedInfo(BaseModel):
    """GTFS feed information"""
    feed_publisher_name: str
    feed_publisher_url: str
    feed_lang: str
    feed_start_date: Optional[date] = None
    feed_end_date: Optional[date] = None
    feed_version: Optional[str] = None
    default_lang: Optional[str] = None
    feed_contact_email: Optional[str] = None
    feed_contact_url: Optional[str] = None