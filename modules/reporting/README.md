# Reporting Module

Generates ISO 14046 compliant water footprint and sustainability reports.

## Features

- **ISO 14046 Reports**: Water footprint assessment reports
- **PDF Generation**: Professional PDF reports with charts and maps
- **Data Visualization**: Embedded charts, tables, and maps
- **Custom Templates**: Configurable report templates
- **Batch Generation**: Generate reports for multiple locations
- **Export Formats**: PDF, HTML, JSON

## ISO 14046 Report Structure

### 1. Executive Summary
- Project overview
- Key findings
- Recommendations

### 2. Methodology
- Data sources
- Analysis methods
- Model specifications

### 3. Water Balance Assessment
- Precipitation analysis
- Evapotranspiration
- Groundwater recharge
- Water availability

### 4. Aquifer Analysis
- Aquifer presence predictions
- Depth classification
- Spatial distribution
- Confidence metrics

### 5. Recharge Forecasting
- Historical trends
- Future projections
- Seasonal patterns
- Uncertainty analysis

### 6. Sustainability Indicators
- Water stress index
- Recharge potential
- Depletion risk
- Management recommendations

### 7. Appendices
- Data tables
- Model performance metrics
- Technical specifications

## Usage

```python
from reporting import ReportGenerator

# Initialize generator
generator = ReportGenerator()

# Generate ISO report
report = generator.generate_iso_report(
    region='Kenya',
    predictions=predictions_data,
    forecasts=forecast_data,
    output_path='reports/kenya_water_assessment.pdf'
)

# Generate summary report
summary = generator.generate_summary(
    data=analysis_data,
    output_path='reports/summary.pdf'
)
```

## Report Templates

### ISO 14046 Template

```python
template = {
    'title': 'Water Footprint Assessment',
    'subtitle': 'ISO 14046 Compliance Report',
    'sections': [
        'executive_summary',
        'methodology',
        'water_balance',
        'aquifer_analysis',
        'forecasting',
        'sustainability',
        'appendices'
    ],
    'include_maps': True,
    'include_charts': True,
    'page_size': 'A4',
    'orientation': 'portrait'
}
```

## Dependencies

- **ReportLab**: PDF generation
- **Matplotlib**: Chart generation
- **Plotly**: Interactive visualizations
- **Jinja2**: Template rendering
- **Pillow**: Image processing

## Testing

```bash
pytest tests/
```
