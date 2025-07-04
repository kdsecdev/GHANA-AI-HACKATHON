import pandas as pd
import numpy as np
import os
import zipfile
import geopandas as gpd
from shapely.geometry import Point, LineString
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, date, time
import gtfs_kit as gk

logger = logging.getLogger(__name__)

class GTFSProcessor:
    """Utility class for processing GTFS data"""
    
    def __init__(self, gtfs_path: str):
        """
        Initialize GTFS processor
        
        Args:
            gtfs_path: Path to GTFS zip file or directory
        """
        self.gtfs_path = gtfs_path
        self.gtfs_data = {}
        self.feed = None
        self.load_gtfs_data()
    
    def load_gtfs_data(self):
        """Load GTFS data from zip file or directory"""
        try:
            if os.path.isfile(self.gtfs_path) and self.gtfs_path.endswith('.zip'):
                # Load from zip file
                self.feed = gk.read_feed(self.gtfs_path, dist_units='km')
            elif os.path.isdir(self.gtfs_path):
                # Load from directory
                self.feed = gk.read_feed(self.gtfs_path, dist_units='km')
            else:
                raise ValueError(f"Invalid GTFS path: {self.gtfs_path}")
            
            # Load individual files
            self._load_required_files()
            self._load_optional_files()
            
            logger.info(f"Successfully loaded GTFS data from {self.gtfs_path}")
            
        except Exception as e:
            logger.error(f"Error loading GTFS data: {e}")
            raise
    
    def _load_required_files(self):
        """Load required GTFS files"""
        required_files = ['agency', 'stops', 'routes', 'trips', 'stop_times', 'calendar']
        
        for file_name in required_files:
            if hasattr(self.feed, file_name):
                self.gtfs_data[file_name] = getattr(self.feed, file_name)
            else:
                logger.warning(f"Required GTFS file {file_name}.txt not found")
    
    def _load_optional_files(self):
        """Load optional GTFS files"""
        optional_files = ['calendar_dates', 'fare_attributes', 'fare_rules', 
                         'shapes', 'frequencies', 'transfers', 'feed_info']
        
        for file_name in optional_files:
            if hasattr(self.feed, file_name):
                self.gtfs_data[file_name] = getattr(self.feed, file_name)
            else:
                logger.info(f"Optional GTFS file {file_name}.txt not found")
    
    def get_routes(self) -> pd.DataFrame:
        """Get all routes from GTFS data"""
        return self.gtfs_data.get('routes', pd.DataFrame())
    
    def get_stops(self) -> pd.DataFrame:
        """Get all stops from GTFS data"""
        return self.gtfs_data.get('stops', pd.DataFrame())
    
    def get_trips(self, route_id: Optional[str] = None) -> pd.DataFrame:
        """Get trips, optionally filtered by route_id"""
        trips = self.gtfs_data.get('trips', pd.DataFrame())
        if route_id and not trips.empty:
            trips = trips[trips['route_id'] == route_id]
        return trips
    
    def get_stop_times(self, trip_id: Optional[str] = None) -> pd.DataFrame:
        """Get stop times, optionally filtered by trip_id"""
        stop_times = self.gtfs_data.get('stop_times', pd.DataFrame())
        if trip_id and not stop_times.empty:
            stop_times = stop_times[stop_times['trip_id'] == trip_id]
        return stop_times
    
    def get_route_stops(self, route_id: str) -> pd.DataFrame:
        """Get all stops for a specific route"""
        trips = self.get_trips(route_id)
        if trips.empty:
            return pd.DataFrame()
        
        trip_ids = trips['trip_id'].unique()
        stop_times = self.get_stop_times()
        route_stop_times = stop_times[stop_times['trip_id'].isin(trip_ids)]
        
        if route_stop_times.empty:
            return pd.DataFrame()
        
        stops = self.get_stops()
        route_stops = stops[stops['stop_id'].isin(route_stop_times['stop_id'].unique())]
        
        return route_stops
    
    def get_shapes(self, shape_id: Optional[str] = None) -> pd.DataFrame:
        """Get shapes, optionally filtered by shape_id"""
        shapes = self.gtfs_data.get('shapes', pd.DataFrame())
        if shape_id and not shapes.empty:
            shapes = shapes[shapes['shape_id'] == shape_id]
        return shapes
    
    def get_calendar(self, service_id: Optional[str] = None) -> pd.DataFrame:
        """Get calendar data, optionally filtered by service_id"""
        calendar = self.gtfs_data.get('calendar', pd.DataFrame())
        if service_id and not calendar.empty:
            calendar = calendar[calendar['service_id'] == service_id]
        return calendar
    
    def get_frequencies(self, trip_id: Optional[str] = None) -> pd.DataFrame:
        """Get frequencies, optionally filtered by trip_id"""
        frequencies = self.gtfs_data.get('frequencies', pd.DataFrame())
        if trip_id and not frequencies.empty:
            frequencies = frequencies[frequencies['trip_id'] == trip_id]
        return frequencies
    
    def get_transfers(self, from_stop_id: Optional[str] = None, 
                     to_stop_id: Optional[str] = None) -> pd.DataFrame:
        """Get transfers, optionally filtered by stop IDs"""
        transfers = self.gtfs_data.get('transfers', pd.DataFrame())
        if from_stop_id and not transfers.empty:
            transfers = transfers[transfers['from_stop_id'] == from_stop_id]
        if to_stop_id and not transfers.empty:
            transfers = transfers[transfers['to_stop_id'] == to_stop_id]
        return transfers
    
    def get_route_geometry(self, route_id: str) -> Optional[LineString]:
        """Get route geometry from shapes"""
        trips = self.get_trips(route_id)
        if trips.empty or 'shape_id' not in trips.columns:
            return None
        
        shape_id = trips['shape_id'].iloc[0]
        if pd.isna(shape_id):
            return None
        
        shapes = self.get_shapes(shape_id)
        if shapes.empty:
            return None
        
        shapes = shapes.sort_values('shape_pt_sequence')
        coords = [(row['shape_pt_lon'], row['shape_pt_lat']) 
                 for _, row in shapes.iterrows()]
        
        return LineString(coords) if len(coords) > 1 else None
    
    def get_stop_geometry(self, stop_id: str) -> Optional[Point]:
        """Get stop geometry"""
        stops = self.get_stops()
        if stops.empty:
            return None
        
        stop = stops[stops['stop_id'] == stop_id]
        if stop.empty:
            return None
        
        stop = stop.iloc[0]
        return Point(stop['stop_lon'], stop['stop_lat'])
    
    def calculate_route_stats(self, route_id: str) -> Dict[str, Any]:
        """Calculate basic statistics for a route"""
        trips = self.get_trips(route_id)
        if trips.empty:
            return {}
        
        route_stops = self.get_route_stops(route_id)
        shapes = self.get_shapes()
        
        stats = {
            'route_id': route_id,
            'total_trips': len(trips),
            'total_stops': len(route_stops),
            'directions': trips['direction_id'].nunique() if 'direction_id' in trips.columns else 1,
            'service_ids': trips['service_id'].nunique(),
            'has_shapes': not shapes.empty and 'shape_id' in trips.columns,
            'wheelchair_accessible_trips': 0,
            'bikes_allowed_trips': 0
        }
        
        if 'wheelchair_accessible' in trips.columns:
            stats['wheelchair_accessible_trips'] = (trips['wheelchair_accessible'] == 1).sum()
        
        if 'bikes_allowed' in trips.columns:
            stats['bikes_allowed_trips'] = (trips['bikes_allowed'] == 1).sum()
        
        return stats
    
    def get_service_dates(self, service_id: str) -> List[date]:
        """Get service dates for a service_id"""
        calendar = self.get_calendar(service_id)
        if calendar.empty:
            return []
        
        service = calendar.iloc[0]
        start_date = pd.to_datetime(service['start_date'], format='%Y%m%d').date()
        end_date = pd.to_datetime(service['end_date'], format='%Y%m%d').date()
        
        # Get active days of week
        active_days = []
        days_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day, weekday in days_map.items():
            if service.get(day, 0) == 1:
                active_days.append(weekday)
        
        # Generate dates
        dates = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in active_days:
                dates.append(current_date)
            current_date = pd.Timedelta(days=1) + current_date
        
        return dates
    
    def validate_gtfs_data(self) -> Dict[str, Any]:
        """Validate GTFS data completeness and consistency"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_counts': {}
        }
        
        # Check required files
        required_files = ['agency', 'stops', 'routes', 'trips', 'stop_times', 'calendar']
        for file_name in required_files:
            if file_name not in self.gtfs_data or self.gtfs_data[file_name].empty:
                validation_results['errors'].append(f"Missing required file: {file_name}.txt")
                validation_results['valid'] = False
            else:
                validation_results['file_counts'][file_name] = len(self.gtfs_data[file_name])
        
        # Check data consistency
        if validation_results['valid']:
            self._validate_data_consistency(validation_results)
        
        return validation_results
    
    def _validate_data_consistency(self, validation_results: Dict[str, Any]):
        """Validate data consistency between files"""
        # Check route references
        trips = self.get_trips()
        routes = self.get_routes()
        
        if not trips.empty and not routes.empty:
            missing_routes = set(trips['route_id']) - set(routes['route_id'])
            if missing_routes:
                validation_results['errors'].append(
                    f"Trips reference missing routes: {list(missing_routes)[:5]}"
                )
        
        # Check stop references
        stop_times = self.get_stop_times()
        stops = self.get_stops()
        
        if not stop_times.empty and not stops.empty:
            missing_stops = set(stop_times['stop_id']) - set(stops['stop_id'])
            if missing_stops:
                validation_results['errors'].append(
                    f"Stop times reference missing stops: {list(missing_stops)[:5]}"
                )
        
        # Check trip references
        if not stop_times.empty and not trips.empty:
            missing_trips = set(stop_times['trip_id']) - set(trips['trip_id'])
            if missing_trips:
                validation_results['errors'].append(
                    f"Stop times reference missing trips: {list(missing_trips)[:5]}"
                )
    
    def export_filtered_gtfs(self, output_path: str, route_ids: List[str]):
        """Export filtered GTFS data for specific routes"""
        # This would create a new GTFS dataset with only the specified routes
        # Implementation depends on specific requirements
        pass
    
    def get_gtfs_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the GTFS feed"""
        summary = {
            'feed_info': {},
            'agencies': len(self.gtfs_data.get('agency', [])),
            'routes': len(self.gtfs_data.get('routes', [])),
            'stops': len(self.gtfs_data.get('stops', [])),
            'trips': len(self.gtfs_data.get('trips', [])),
            'stop_times': len(self.gtfs_data.get('stop_times', [])),
            'shapes': len(self.gtfs_data.get('shapes', [])),
            'calendar_services': len(self.gtfs_data.get('calendar', [])),
            'has_frequencies': 'frequencies' in self.gtfs_data,
            'has_transfers': 'transfers' in self.gtfs_data,
            'has_feed_info': 'feed_info' in self.gtfs_data,
            'route_types': []
        }
        
        # Get route types
        routes = self.get_routes()
        if not routes.empty and 'route_type' in routes.columns:
            summary['route_types'] = routes['route_type'].unique().tolist()
        
        # Get feed info
        if 'feed_info' in self.gtfs_data:
            feed_info = self.gtfs_data['feed_info']
            if not feed_info.empty:
                summary['feed_info'] = feed_info.iloc[0].to_dict()
        
        return summary