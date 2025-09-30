"""Main script for preprocessing module."""

import logging
import argparse
import os
from pathlib import Path

from preprocessor import DataPreprocessor
from config import PreprocessingConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function for preprocessing."""
    parser = argparse.ArgumentParser(description='AquaPredict Data Preprocessing')
    parser.add_argument('--input-dir', type=str, default='./data/raw',
                       help='Input directory with raw data')
    parser.add_argument('--output-dir', type=str, default='./data/processed',
                       help='Output directory for processed data')
    parser.add_argument('--clean', action='store_true',
                       help='Clean data (remove invalid values)')
    parser.add_argument('--fill-missing', action='store_true',
                       help='Fill missing values')
    parser.add_argument('--remove-outliers', action='store_true',
                       help='Remove outliers')
    parser.add_argument('--normalize', action='store_true',
                       help='Normalize data')
    parser.add_argument('--resample', action='store_true',
                       help='Resample to target resolution')
    
    args = parser.parse_args()
    
    # Initialize
    config = PreprocessingConfig()
    config.raw_data_dir = args.input_dir
    config.processed_data_dir = args.output_dir
    
    preprocessor = DataPreprocessor(config)
    
    logger.info("=" * 80)
    logger.info("AquaPredict Data Preprocessing")
    logger.info("=" * 80)
    logger.info(f"Input directory: {args.input_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info("=" * 80)
    
    # Find all GeoTIFF files in input directory
    input_path = Path(args.input_dir)
    tif_files = list(input_path.glob("*.tif")) + list(input_path.glob("*.tiff"))
    
    if not tif_files:
        logger.warning(f"No GeoTIFF files found in {args.input_dir}")
        return
    
    logger.info(f"Found {len(tif_files)} files to process")
    
    try:
        for tif_file in tif_files:
            logger.info(f"\n>>> Processing: {tif_file.name}")
            
            output_file = Path(args.output_dir) / tif_file.name
            
            # Clean data
            if args.clean:
                logger.info("  - Cleaning data...")
                data = preprocessor.clean_raster(str(tif_file))
            
            # Resample
            if args.resample:
                logger.info("  - Resampling...")
                temp_output = str(output_file).replace('.tif', '_resampled.tif')
                preprocessor.resample_raster(str(tif_file), temp_output)
                tif_file = Path(temp_output)
            
            # Load data for further processing
            data = preprocessor.clean_raster(str(tif_file))
            
            # Fill missing values
            if args.fill_missing:
                logger.info("  - Filling missing values...")
                data = preprocessor.fill_missing(data)
            
            # Remove outliers
            if args.remove_outliers:
                logger.info("  - Removing outliers...")
                data = preprocessor.remove_outliers(data, replace_with='median')
            
            # Normalize
            if args.normalize:
                logger.info("  - Normalizing...")
                data = preprocessor.normalize(data)
            
            # Save processed data
            # Note: In production, implement proper saving with rasterio
            logger.info(f"  ✓ Processed: {tif_file.name}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ Preprocessing completed successfully!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"✗ Error during preprocessing: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
