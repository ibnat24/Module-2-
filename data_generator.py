"""
Healthcare ER Patient Flow - Data Generator
Generates mock historical data based on actual gameplay patterns
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class ERDataGenerator:
    """Generate realistic ER patient arrival data based on gameplay patterns"""
    
    def __init__(self):
        # Actual gameplay data (23 rounds)
        self.actual_data = {
            'emergency_walkin': [2,4,3,8,4,5,5,7,5,4,4,5,6,4,6,2,2,1,7,1,7,4,2],
            'emergency_ambulance': [0,1,1,2,0,2,0,0,1,2,1,3,2,2,2,3,1,1,0,1,0,2,1],
            'surgery': [3,1,1,0,2,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            'critical_care': [1,1,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            'step_down': [1,2,1,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1]
        }
        
        # Calculate statistics from actual data
        self.stats = self._calculate_stats()
    
    def _calculate_stats(self):
        """Calculate statistical properties of actual gameplay data"""
        stats = {}
        for dept, values in self.actual_data.items():
            stats[dept] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': min(values),
                'max': max(values),
                'early_mean': np.mean(values[:8]),  # First 8 rounds
                'mid_mean': np.mean(values[8:16]),   # Middle 8 rounds
                'late_mean': np.mean(values[16:])    # Last 7 rounds
            }
        return stats
    
    def generate_round_arrivals(self, dept, round_num, variation_factor=0.2):
        """
        Generate arrivals for a specific department and round
        
        Args:
            dept: Department name
            round_num: Round number (0-22)
            variation_factor: How much to vary from base patterns (0-1)
        """
        stat = self.stats[dept]
        
        # Determine base rate based on round position
        if round_num < 8:
            base_mean = stat['early_mean']
        elif round_num < 16:
            base_mean = stat['mid_mean']
        else:
            base_mean = stat['late_mean']
        
        # Add variation
        std_dev = stat['std'] * (1 + variation_factor)
        
        # Generate value (ensure non-negative integer)
        value = max(0, int(np.random.normal(base_mean, std_dev)))
        
        # Apply department-specific constraints
        if dept in ['surgery', 'critical_care']:
            # These departments rare after round 8
            if round_num > 8:
                value = np.random.poisson(0.1)  # Very rare
        
        if dept == 'step_down':
            # Front-loaded with occasional late arrivals
            if round_num > 10 and round_num < 18:
                value = 0 if np.random.random() > 0.1 else value
        
        return min(value, stat['max'] + 2)  # Cap at reasonable max
    
    def generate_session(self, num_rounds=23, session_id=1, variation=0.2):
        """Generate a complete gameplay session"""
        session_data = {
            'round': list(range(1, num_rounds + 1)),
            'session_id': [session_id] * num_rounds,
            'emergency_walkin': [],
            'emergency_ambulance': [],
            'surgery': [],
            'critical_care': [],
            'step_down': []
        }
        
        for round_num in range(num_rounds):
            for dept in ['emergency_walkin', 'emergency_ambulance', 'surgery', 'critical_care', 'step_down']:
                arrivals = self.generate_round_arrivals(dept, round_num, variation)
                session_data[dept].append(arrivals)
        
        return pd.DataFrame(session_data)
    
    def generate_multiple_sessions(self, num_sessions=5, num_rounds=23):
        """Generate multiple gameplay sessions with varying patterns"""
        all_sessions = []
        
        # First session is actual data
        actual_df = pd.DataFrame(self.actual_data)
        actual_df.insert(0, 'round', list(range(1, len(actual_df) + 1)))
        actual_df.insert(1, 'session_id', 0)
        all_sessions.append(actual_df)
        
        # Generate additional sessions with varying intensities
        for session_id in range(1, num_sessions):
            variation = 0.15 + (session_id * 0.05)  # Increasing variation
            session_df = self.generate_session(num_rounds, session_id, variation)
            all_sessions.append(session_df)
        
        return pd.concat(all_sessions, ignore_index=True)
    
    def generate_real_time_data(self, current_round, historical_df):
        """
        Generate real-time data for current round with some randomness
        
        Args:
            current_round: Current round number
            historical_df: Historical data for reference
        """
        # Calculate averages from historical data for this round
        round_data = historical_df[historical_df['round'] == current_round]
        
        current_data = {}
        for dept in ['emergency_walkin', 'emergency_ambulance', 'surgery', 'critical_care', 'step_down']:
            if len(round_data) > 0:
                mean_val = round_data[dept].mean()
                std_val = round_data[dept].std() if round_data[dept].std() > 0 else 1
                current_data[dept] = max(0, int(np.random.normal(mean_val, std_val)))
            else:
                # Fallback to overall stats
                current_data[dept] = self.generate_round_arrivals(dept, current_round - 1)
        
        return current_data
    
    def export_to_csv(self, df, filename='er_historical_data.csv'):
        """Export generated data to CSV"""
        df.to_csv(filename, index=False)
        print(f"Data exported to {filename}")
        return filename


if __name__ == "__main__":
    # Generate data
    generator = ERDataGenerator()
    
    # Generate 5 sessions (1 actual + 4 mock)
    historical_data = generator.generate_multiple_sessions(num_sessions=5)
    
    print("Generated Historical Data:")
    print(f"Total records: {len(historical_data)}")
    print(f"Sessions: {historical_data['session_id'].unique()}")
    print("\nSample data:")
    print(historical_data.head(10))
    print("\nStatistics by department:")
    print(historical_data[['emergency_walkin', 'emergency_ambulance', 'surgery', 'critical_care', 'step_down']].describe())
    
    # Export
    generator.export_to_csv(historical_data, '/home/claude/er_historical_data.csv')
