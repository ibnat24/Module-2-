# 🚀 Quick Start Guide

## What You Have

A complete ER Patient Flow Dashboard with:
- ✅ Historical data generator (using your actual gameplay data)
- ✅ Predictive analytics engine (ensemble forecasting)
- ✅ Interactive web dashboard (Plotly Dash)
- ✅ Standalone demo script
- ✅ Full documentation

## Files Included

1. **dashboard.py** - Main interactive web dashboard
2. **data_generator.py** - Mock data generation module
3. **predictive_analytics.py** - Forecasting and analytics
4. **demo.py** - Standalone demonstration (no web server needed)
5. **requirements.txt** - Python dependencies
6. **README.md** - Complete documentation
7. **er_historical_data.csv** - Generated historical data

## Getting Started (3 Options)

### Option 1: Run the Demo (Easiest - No Installation)
```bash
python demo.py
```
This shows all features in your terminal without needing any packages installed.

### Option 2: Run the Web Dashboard (Recommended)
```bash
# Install dependencies
pip install -r requirements.txt

# Run dashboard
python dashboard.py

# Open in browser
http://127.0.0.1:8050
```

### Option 3: Test Components Individually
```bash
# Test data generation
python data_generator.py

# Test analytics
python predictive_analytics.py
```

## Dashboard Features

### 📊 Real-Time Monitoring
- Patient count by department
- Capacity utilization heat map
- Current staffing levels
- Performance metrics

### 🔮 Predictive Analytics
- 4-round ahead forecast
- Ensemble method (MA + Time + Trend)
- Confidence intervals
- Historical patterns

### ⚠️ Alerts & Recommendations
- Surge detection
- Staffing recommendations
- Bottleneck identification
- Resource reallocation

### 🎮 Gameplay Controls
- Manual round selection
- Auto-simulate next round
- Real-time patient generation
- Live metric updates

## For Your Module 2 Report

### Integration of Skills (Breadth)
Your dashboard demonstrates:
- **MSE 202**: Forecasting, confidence intervals, statistical analysis
- **MSE 212**: Discrete-event simulation principles
- **MSE 335**: Demand forecasting, capacity planning
- **MSE 401**: Resource allocation optimization
- **MSE 411**: Queue management, service systems
- **MSE 432**: Predictive analytics, decision support

### Methodology Rigor (Depth)
- Ensemble forecasting (3 methods combined)
- Statistical validation (confidence intervals)
- Real gameplay data as baseline
- Surge detection algorithms
- Dynamic capacity planning

### Analysis & Recommendations
The dashboard provides:
- Actionable staffing recommendations
- Advance warning of surges (4 rounds ahead)
- Department-specific insights
- Evidence-based decision support

## Testing for Gameplay 2

1. **Run baseline** (no dashboard): Track metrics
2. **Use dashboard predictions**: Pre-allocate resources
3. **Follow recommendations**: Adjust staffing
4. **Compare results**: Measure improvement

### Metrics to Track
- Wait times per department
- Patients successfully treated
- Bottleneck frequency
- Resource utilization
- Team coordination time

## Customization

### Adjust Capacity
Edit `CAPACITY_CONFIG` in dashboard.py:
```python
CAPACITY_CONFIG = {
    'emergency_walkin': {
        'patients_per_nurse': 4,
        'patients_per_doctor': 8,
        'beds': 15
    }
}
```

### Change Forecast Horizon
Modify in dashboard.py:
```python
future_forecasts = analytics.forecast_next_n_rounds(current_round, n=6)  # 6 rounds
```

### Alert Sensitivity
Adjust in predictive_analytics.py:
```python
alerts = analytics.detect_surge(forecasts, threshold_percentile=70)  # More sensitive
```

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Port 8050 already in use
Edit dashboard.py:
```python
app.run_server(port=8051)  # Change port
```

### No data showing
Check that data_generator.py ran successfully:
```bash
python data_generator.py
```

## Next Steps

1. ✅ Run demo.py to see all features
2. ✅ Install dependencies for web dashboard
3. ✅ Customize capacity settings for your gameplay
4. ✅ Test during Gameplay 2
5. ✅ Document results for presentation/report

## Questions?

Refer to README.md for detailed documentation or check:
- Dashboard comments (inline documentation)
- Demo output (shows expected behavior)
- Generated CSV file (data structure)

---

**Ready to impress your team and prof! 🎯**
