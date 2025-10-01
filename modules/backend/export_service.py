"""
Export Service
Handles data export in various formats (CSV, JSON, GeoJSON, PDF).
"""

import json
import csv
import io
import logging
from typing import Dict, Any, List
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting data in various formats."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def export_csv(self, data: Dict[str, Any], export_type: str) -> str:
        """
        Export data as CSV.
        
        Args:
            data: Data to export
            export_type: Type of export (prediction, forecast, history)
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        
        if export_type == "prediction":
            writer = csv.writer(output)
            writer.writerow([
                'Latitude', 'Longitude', 'Prediction', 'Probability',
                'Confidence_Low', 'Confidence_High', 'Geological_Formation',
                'Porosity', 'Recommended_Depth', 'Timestamp'
            ])
            
            loc = data.get('location', {})
            ci = data.get('confidence_interval', [0, 0])
            
            writer.writerow([
                loc.get('lat', ''),
                loc.get('lon', ''),
                data.get('prediction', ''),
                data.get('probability', ''),
                ci[0] if len(ci) > 0 else '',
                ci[1] if len(ci) > 1 else '',
                data.get('geological_formation', ''),
                data.get('estimated_porosity', ''),
                data.get('recommended_drilling_depth', ''),
                data.get('timestamp', '')
            ])
            
            # Add depth bands
            output.write('\n\nDepth Bands\n')
            writer = csv.writer(output)
            writer.writerow(['Depth_Range', 'Probability', 'Quality', 'Yield_LPM', 'Aquifer_Type', 'Recharge_Rate'])
            
            for band in data.get('depth_bands', []):
                writer.writerow([
                    band.get('depth_range', ''),
                    band.get('probability', ''),
                    band.get('quality', ''),
                    band.get('yield_lpm', ''),
                    band.get('aquifer_type', ''),
                    band.get('recharge_rate', '')
                ])
        
        elif export_type == "forecast":
            writer = csv.writer(output)
            writer.writerow([
                'Month', 'Precipitation_mm', 'Recharge_mm', 'Extraction_mm',
                'Net_Change_mm', 'Cumulative_Storage_mm', 'Confidence'
            ])
            
            for item in data.get('forecast', []):
                writer.writerow([
                    item.get('month', ''),
                    item.get('precipitation_mm', ''),
                    item.get('recharge_mm', ''),
                    item.get('extraction_mm', ''),
                    item.get('net_change_mm', ''),
                    item.get('cumulative_storage_mm', ''),
                    item.get('confidence', '')
                ])
        
        elif export_type == "history":
            writer = csv.writer(output)
            writer.writerow([
                'Timestamp', 'Latitude', 'Longitude', 'Prediction',
                'Probability', 'Data_Source'
            ])
            
            for item in data.get('history', []):
                loc = item.get('location', {})
                writer.writerow([
                    item.get('timestamp', ''),
                    loc.get('lat', ''),
                    loc.get('lon', ''),
                    item.get('prediction', ''),
                    item.get('probability', ''),
                    item.get('data_source', '')
                ])
        
        return output.getvalue()
    
    def export_json(self, data: Dict[str, Any], include_metadata: bool = True) -> str:
        """
        Export data as JSON.
        
        Args:
            data: Data to export
            include_metadata: Include metadata
            
        Returns:
            JSON string
        """
        if include_metadata:
            export_data = {
                "metadata": {
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "source": "AquaPredict API v2.0",
                    "format": "JSON"
                },
                "data": data
            }
        else:
            export_data = data
        
        return json.dumps(export_data, indent=2)
    
    def export_geojson(self, data: Dict[str, Any]) -> str:
        """
        Export data as GeoJSON.
        
        Args:
            data: Data to export
            
        Returns:
            GeoJSON string
        """
        features = []
        
        # Handle single prediction
        if 'location' in data and 'prediction' in data:
            loc = data['location']
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [loc.get('lon'), loc.get('lat')]
                },
                "properties": {
                    "prediction": data.get('prediction'),
                    "probability": data.get('probability'),
                    "geological_formation": data.get('geological_formation'),
                    "recommended_depth": data.get('recommended_drilling_depth'),
                    "timestamp": data.get('timestamp')
                }
            }
            features.append(feature)
        
        # Handle history/multiple predictions
        elif 'history' in data:
            for item in data['history']:
                loc = item.get('location', {})
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [loc.get('lon'), loc.get('lat')]
                    },
                    "properties": {
                        "prediction": item.get('prediction'),
                        "probability": item.get('probability'),
                        "timestamp": item.get('timestamp')
                    }
                }
                features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "generated": datetime.utcnow().isoformat(),
                "source": "AquaPredict"
            },
            "features": features
        }
        
        return json.dumps(geojson, indent=2)
    
    def export_pdf(self, data: Dict[str, Any], export_type: str) -> bytes:
        """
        Export data as PDF report.
        
        Args:
            data: Data to export
            export_type: Type of export
            
        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30
        )
        
        story.append(Paragraph("AquaPredict Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Metadata
        meta_data = [
            ['Report Type:', export_type.title()],
            ['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')],
            ['Platform:', 'AquaPredict v2.0']
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(meta_table)
        story.append(Spacer(1, 0.3*inch))
        
        if export_type == "prediction":
            self._add_prediction_content(story, data)
        elif export_type == "forecast":
            self._add_forecast_content(story, data)
        elif export_type == "report":
            self._add_full_report_content(story, data)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.read()
    
    def _add_prediction_content(self, story: List, data: Dict[str, Any]):
        """Add prediction content to PDF."""
        # Location
        story.append(Paragraph("Location Information", self.styles['Heading2']))
        loc = data.get('location', {})
        
        loc_data = [
            ['Latitude:', f"{loc.get('lat', 'N/A')}°"],
            ['Longitude:', f"{loc.get('lon', 'N/A')}°"],
            ['Data Source:', data.get('data_source', 'N/A').upper()]
        ]
        
        loc_table = Table(loc_data, colWidths=[2*inch, 4*inch])
        loc_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(loc_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Prediction Results
        story.append(Paragraph("Prediction Results", self.styles['Heading2']))
        
        prob = data.get('probability', 0)
        ci = data.get('confidence_interval', [0, 0])
        
        pred_data = [
            ['Aquifer Presence:', data.get('prediction', 'N/A').upper()],
            ['Probability:', f"{prob:.1%}"],
            ['Confidence Interval:', f"{ci[0]:.1%} - {ci[1]:.1%}"],
            ['Geological Formation:', data.get('geological_formation', 'N/A')],
            ['Estimated Porosity:', data.get('estimated_porosity', 'N/A')],
            ['Recommended Depth:', data.get('recommended_drilling_depth', 'N/A')]
        ]
        
        pred_table = Table(pred_data, colWidths=[2.5*inch, 3.5*inch])
        pred_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(pred_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Depth Bands
        story.append(Paragraph("Depth Band Analysis", self.styles['Heading2']))
        
        depth_data = [['Depth', 'Probability', 'Quality', 'Yield (LPM)', 'Type']]
        
        for band in data.get('depth_bands', []):
            depth_data.append([
                band.get('depth_range', ''),
                f"{band.get('probability', 0):.1%}",
                band.get('quality', ''),
                band.get('yield_lpm', ''),
                band.get('aquifer_type', '')
            ])
        
        depth_table = Table(depth_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.5*inch])
        depth_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(depth_table)
    
    def _add_forecast_content(self, story: List, data: Dict[str, Any]):
        """Add forecast content to PDF."""
        story.append(Paragraph("Recharge Forecast", self.styles['Heading2']))
        
        # Summary
        summary = data.get('summary', {})
        summary_data = [
            ['Total Recharge:', f"{summary.get('total_recharge_mm', 0):.1f} mm"],
            ['Total Extraction:', f"{summary.get('total_extraction_mm', 0):.1f} mm"],
            ['Net Change:', f"{summary.get('net_change_mm', 0):.1f} mm"],
            ['Sustainability:', summary.get('sustainability_status', 'N/A').upper()]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Monthly forecast (first 12 months)
        story.append(Paragraph("Monthly Forecast", self.styles['Heading3']))
        
        forecast_data = [['Month', 'Precip (mm)', 'Recharge (mm)', 'Net Change (mm)']]
        
        for item in data.get('forecast', [])[:12]:
            forecast_data.append([
                item.get('month', ''),
                f"{item.get('precipitation_mm', 0):.1f}",
                f"{item.get('recharge_mm', 0):.1f}",
                f"{item.get('net_change_mm', 0):.1f}"
            ])
        
        forecast_table = Table(forecast_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        forecast_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(forecast_table)
    
    def _add_full_report_content(self, story: List, data: Dict[str, Any]):
        """Add full report content to PDF."""
        # This would combine prediction and forecast data
        if 'prediction' in data:
            self._add_prediction_content(story, data['prediction'])
        
        if 'forecast' in data:
            story.append(PageBreak())
            self._add_forecast_content(story, data['forecast'])
