"""Main script for data ingestion module."""

import logging
import argparse
from datetime import datetime

from gee_fetcher import GEEDataFetcher
from data_exporter import DataExporter
from config import IngestionConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function for data ingestion."""
    parser = argparse.ArgumentParser(description='AquaPredict Data Ingestion')
    parser.add_argument('--dataset', type=str, required=True,
                       choices=['precipitation', 'temperature', 'elevation', 'landcover', 'all'],
                       help='Dataset to fetch')
    parser.add_argument('--start-date', type=str, default='2020-01-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='2023-12-31',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', type=str, default='./data/raw',
                       help='Output directory')
    parser.add_argument('--format', type=str, default='geotiff',
                       choices=['geotiff', 'netcdf'],
                       help='Output format')
    
    args = parser.parse_args()
    
    # Initialize
    config = IngestionConfig()
    fetcher = GEEDataFetcher(config)
    exporter = DataExporter(config)
    
    logger.info("=" * 80)
    logger.info("AquaPredict Data Ingestion - Kenya Pilot")
    logger.info("=" * 80)
    logger.info(f"Dataset: {args.dataset}")
    logger.info(f"Date range: {args.start_date} to {args.end_date}")
    logger.info(f"Region: Kenya (bounds: {config.region_bounds})")
    logger.info(f"Resolution: {config.grid_resolution_km} km")
    logger.info("=" * 80)
    
    try:
        if args.dataset in ['precipitation', 'all']:
            logger.info("\n>>> Fetching Precipitation Data (CHIRPS)")
            precip_image = fetcher.fetch_precipitation(
                args.start_date,
                args.end_date,
                aggregation='monthly'
            )
            
            output_path = f"{args.output_dir}/kenya_precipitation.tif"
            if args.format == 'geotiff':
                exporter.export_to_geotiff(precip_image, output_path)
            else:
                output_path = output_path.replace('.tif', '.nc')
                exporter.export_to_netcdf(precip_image, output_path)
            
            logger.info(f"✓ Precipitation data saved to: {output_path}")
        
        if args.dataset in ['temperature', 'all']:
            logger.info("\n>>> Fetching Temperature Data (ERA5)")
            temp_image = fetcher.fetch_temperature(
                args.start_date,
                args.end_date
            )
            
            output_path = f"{args.output_dir}/kenya_temperature.tif"
            if args.format == 'geotiff':
                exporter.export_to_geotiff(temp_image, output_path)
            else:
                output_path = output_path.replace('.tif', '.nc')
                exporter.export_to_netcdf(temp_image, output_path)
            
            logger.info(f"✓ Temperature data saved to: {output_path}")
        
        if args.dataset in ['elevation', 'all']:
            logger.info("\n>>> Fetching Elevation Data (SRTM)")
            elev_image = fetcher.fetch_elevation()
            
            output_path = f"{args.output_dir}/kenya_elevation.tif"
            if args.format == 'geotiff':
                exporter.export_to_geotiff(elev_image, output_path)
            else:
                output_path = output_path.replace('.tif', '.nc')
                exporter.export_to_netcdf(elev_image, output_path)
            
            logger.info(f"✓ Elevation data saved to: {output_path}")
        
        if args.dataset in ['landcover', 'all']:
            logger.info("\n>>> Fetching Land Cover Data (ESA WorldCover)")
            lc_image = fetcher.fetch_land_cover(year=2020)
            
            output_path = f"{args.output_dir}/kenya_landcover.tif"
            if args.format == 'geotiff':
                exporter.export_to_geotiff(lc_image, output_path)
            else:
                output_path = output_path.replace('.tif', '.nc')
                exporter.export_to_netcdf(lc_image, output_path)
            
            logger.info(f"✓ Land cover data saved to: {output_path}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ Data ingestion completed successfully!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"✗ Error during data ingestion: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
