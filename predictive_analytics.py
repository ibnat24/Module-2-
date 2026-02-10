"""
Healthcare ER Patient Flow - Predictive Analytics
Forecasting models for patient arrivals and bottleneck detection
"""

import numpy as np
import pandas as pd
from scipy import stats

class ERPredictiveAnalytics:
    """Predictive analytics for ER patient flow"""
    
    def __init__(self, historical_data):
        """
        Initialize with historical data
        
        Args:
            historical_data: DataFrame with columns [session_id, round, emergency_walkin, 
                            emergency_ambulance, surgery, critical_care, step_down]
        """
        self.historical_data = historical_data
        self.departments = ['emergency_walkin', 'emergency_ambulance', 'surgery', 'critical_care', 'step_down']
        self.forecast_cache = {}
    
    def moving_average_forecast(self, dept, current_round, window=3):
        """
        Simple moving average forecast
        
        Args:
            dept: Department name
            current_round: Current round number
            window: Number of previous rounds to average
        """
        if current_round <= 1:
            # Use historical average for first round
            return self.historical_data[dept].mean()
        
        # Get data from recent rounds across all sessions
        recent_data = self.historical_data[
            (self.historical_data['round'] >= max(1, current_round - window)) & 
            (self.historical_data['round'] < current_round)
        ][dept]
        
        if len(recent_data) == 0:
            return self.historical_data[dept].mean()
        
        return recent_data.mean()
    
    def time_based_forecast(self, dept, current_round):
        """
        Time-based forecast using historical patterns for this specific round
        
        Args:
            dept: Department name
            current_round: Current round number
        """
        # Get all historical data for this specific round
        round_data = self.historical_data[self.historical_data['round'] == current_round][dept]
        
        if len(round_data) == 0:
            return self.historical_data[dept].mean()
        
        # Return mean with confidence interval
        mean_forecast = round_data.mean()
        std_forecast = round_data.std() if len(round_data) > 1 else round_data.mean() * 0.3
        
        return {
            'forecast': mean_forecast,
            'lower_bound': max(0, mean_forecast - std_forecast),
            'upper_bound': mean_forecast + std_forecast,
            'confidence': 0.68  # ~68% confidence (1 std dev)
        }
    
    def trend_forecast(self, dept, current_round, lookback=5):
        """
        Trend-based forecast using linear regression on recent data
        
        Args:
            dept: Department name
            current_round: Current round number
            lookback: How many rounds to look back
        """
        if current_round <= 2:
            return self.moving_average_forecast(dept, current_round)
        
        # Get recent rounds data
        recent_rounds = self.historical_data[
            (self.historical_data['round'] >= max(1, current_round - lookback)) & 
            (self.historical_data['round'] < current_round)
        ].groupby('round')[dept].mean().reset_index()
        
        if len(recent_rounds) < 2:
            return self.moving_average_forecast(dept, current_round)
        
        # Simple linear regression
        x = recent_rounds['round'].values
        y = recent_rounds[dept].values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Forecast for current round
        forecast = slope * current_round + intercept
        
        return max(0, forecast)
    
    def ensemble_forecast(self, dept, current_round):
        """
        Ensemble forecast combining multiple methods
        
        Args:
            dept: Department name
            current_round: Current round number
        """
        # Get forecasts from different methods
        ma_forecast = self.moving_average_forecast(dept, current_round, window=3)
        time_forecast = self.time_based_forecast(dept, current_round)
        trend_forecast = self.trend_forecast(dept, current_round, lookback=5)
        
        # Extract forecast value if dict
        time_value = time_forecast['forecast'] if isinstance(time_forecast, dict) else time_forecast
        
        # Weighted average (time-based gets more weight as it's most relevant)
        forecast = (0.4 * time_value + 0.3 * ma_forecast + 0.3 * trend_forecast)
        
        # Calculate confidence bounds
        if isinstance(time_forecast, dict):
            lower = time_forecast['lower_bound']
            upper = time_forecast['upper_bound']
        else:
            std = self.historical_data[dept].std()
            lower = max(0, forecast - std)
            upper = forecast + std
        
        return {
            'forecast': round(forecast, 1),
            'lower_bound': round(lower, 1),
            'upper_bound': round(upper, 1),
            'methods': {
                'moving_average': round(ma_forecast, 1),
                'time_based': round(time_value, 1),
                'trend': round(trend_forecast, 1)
            }
        }
    
    def forecast_all_departments(self, current_round):
        """Generate forecasts for all departments"""
        forecasts = {}
        for dept in self.departments:
            forecasts[dept] = self.ensemble_forecast(dept, current_round)
        
        return forecasts
    
    def forecast_next_n_rounds(self, current_round, n=4):
        """
        Forecast next N rounds for all departments
        
        Args:
            current_round: Current round number
            n: Number of rounds to forecast ahead
        """
        forecast_horizon = {}
        
        for future_round in range(current_round, current_round + n):
            forecast_horizon[future_round] = self.forecast_all_departments(future_round)
        
        return forecast_horizon
    
    def detect_surge(self, forecast_data, threshold_percentile=75):
        """
        Detect potential surge situations
        
        Args:
            forecast_data: Forecast dictionary for a round
            threshold_percentile: Percentile to define "high" arrivals
        """
        alerts = []
        
        for dept, forecast in forecast_data.items():
            # Calculate historical percentile thresholds
            hist_data = self.historical_data[dept]
            threshold = np.percentile(hist_data, threshold_percentile)
            
            forecast_value = forecast['forecast'] if isinstance(forecast, dict) else forecast
            
            # Check if forecast exceeds threshold
            if forecast_value > threshold:
                severity = 'HIGH' if forecast_value > np.percentile(hist_data, 90) else 'MODERATE'
                alerts.append({
                    'department': dept,
                    'forecast': forecast_value,
                    'threshold': threshold,
                    'severity': severity,
                    'message': f"{dept.replace('_', ' ').title()}: Expected {forecast_value:.1f} patients (threshold: {threshold:.1f})"
                })
        
        return alerts
    
    def calculate_capacity_recommendations(self, forecasts, capacity_config):
        """
        Calculate staffing recommendations based on forecasts
        
        Args:
            forecasts: Dictionary of forecasts by department
            capacity_config: Dict with department capacities and staff ratios
                e.g., {'emergency_walkin': {'patients_per_nurse': 4, 'patients_per_doctor': 6}}
        """
        recommendations = {}
        
        for dept, forecast in forecasts.items():
            if dept not in capacity_config:
                continue
            
            config = capacity_config[dept]
            forecast_value = forecast['forecast'] if isinstance(forecast, dict) else forecast
            
            # Calculate needed staff
            nurses_needed = np.ceil(forecast_value / config.get('patients_per_nurse', 4))
            doctors_needed = np.ceil(forecast_value / config.get('patients_per_doctor', 6))
            
            recommendations[dept] = {
                'expected_patients': forecast_value,
                'nurses_recommended': int(nurses_needed),
                'doctors_recommended': int(doctors_needed)
            }
        
        return recommendations
    
    def get_summary_statistics(self):
        """Get summary statistics of historical data"""
        summary = {}
        
        for dept in self.departments:
            dept_data = self.historical_data[dept]
            summary[dept] = {
                'mean': dept_data.mean(),
                'median': dept_data.median(),
                'std': dept_data.std(),
                'min': dept_data.min(),
                'max': dept_data.max(),
                'p25': np.percentile(dept_data, 25),
                'p75': np.percentile(dept_data, 75),
                'p90': np.percentile(dept_data, 90)
            }
        
        return summary


if __name__ == "__main__":
    # Example usage
    from data_generator import ERDataGenerator
    
    # Generate historical data
    generator = ERDataGenerator()
    historical_data = generator.generate_multiple_sessions(num_sessions=5)
    
    # Initialize analytics
    analytics = ERPredictiveAnalytics(historical_data)
    
    # Test forecasting
    current_round = 10
    print(f"\n=== Forecasts for Round {current_round} ===")
    forecasts = analytics.forecast_all_departments(current_round)
    for dept, forecast in forecasts.items():
        print(f"\n{dept.replace('_', ' ').title()}:")
        print(f"  Forecast: {forecast['forecast']:.1f} patients")
        print(f"  Range: {forecast['lower_bound']:.1f} - {forecast['upper_bound']:.1f}")
    
    # Test surge detection
    print(f"\n=== Surge Alerts ===")
    alerts = analytics.detect_surge(forecasts)
    if alerts:
        for alert in alerts:
            print(f"  [{alert['severity']}] {alert['message']}")
    else:
        print("  No surge alerts")
    
    # Multi-round forecast
    print(f"\n=== Next 4 Rounds Forecast ===")
    horizon = analytics.forecast_next_n_rounds(current_round, n=4)
    for round_num, round_forecasts in horizon.items():
        total = sum([f['forecast'] for f in round_forecasts.values()])
        print(f"  Round {round_num}: {total:.1f} total patients expected")
