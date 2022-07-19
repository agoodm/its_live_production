"""
Script to rename directory paths in existing catalog geojson files as stored in
AWS S3 bucket.

It accepts S3 path with geojson files to modify.
"""
import copy
import json
import logging
import math
import os
from pathlib import Path
import s3fs

from grid import Bounds
import itslive_utils
from itscube_types import CubeJson, FilenamePrefix, BatchVars

AWS_PREFIX = 'its-live-data'

# Path to store original and updated catalog geojson files
S3_INPUT_PATH = 'its-live-data/catalog_geojson/landsat/v01'
S3_OUTPUT_PATH = 'its-live-data/catalog_geojson/landsatOLI/v01'
JSON_PATTERN = 'imgpair_*.json'

# Path to original and updated v01 granules
INPUT_FILE_PATH = 'landsat/v00.0'
OUTPUT_FILE_PATH = 'landsatOLI/v01'

def rename_granule_paths():
    """
    Replace 'landsat/v00.0' directory with 'landsatOLI/v01' for all v01 granules listed in
    found catalog geojson files to correspond to the granules location within S3 bucket.
    """
    # Collect existing json files in S3 bucket
    s3_in = s3fs.S3FileSystem(anon=True)
    s3_out = s3fs.S3FileSystem()

    # Fix paths in skipped_granules_landsat.json and used_granules_landsat.json files
    for each in ["skipped_granules_landsat.json", "used_granules_landsat.json"]:
        with s3_in.open(each, 'r') as fhandle:
            all_granules = json.load(fhandle)

            fixed_granules = []
            for each_path in all_granules:
                fixed_granules.append(each_path.replace(INPUT_FILE_PATH, OUTPUT_FILE_PATH))

            output_filename = os.path.join(S3_OUTPUT_PATH, os.path.basename(each))
            logging.info(f'Writing updated geojson {each} to {output_filename}...')
            with s3_out.open(output_filename, 'w') as outf:
                json.dump(fixed_granules, outf)

    all_files = s3_in.glob(os.path.join(S3_INPUT_PATH, JSON_PATTERN))
    all_files.sort()

    logging.info(f'Collected len(all_files) geojson catalogs')

    for each in all_files:
        logging.info(f'Changing {each}')

        with s3_in.open(each, 'r') as fhandle:
            all_granules = json.load(fhandle)

            for each_granule in all_granules[CubeJson.FEATURES]:
                # Example of data cube definition in json file
                # "properties": {
                #     "fill-opacity": 1.0,
                #     "fill": "red",
                #     "roi_percent_coverage": 0.0,
                #     "data_epsg": "EPSG:32701",
                #     "geometry_epsg": {
                #         "type": "Polygon",
                #         "coordinates": [
                #             [
                #                 [
                #                     100000,
                #                     7100000
                #                 ],
                #                 [
                #                     200000,
                #                     7100000
                #                 ],
                #                 [
                #                     200000,
                #                     7200000
                #                 ],
                #                 [
                #                     100000,
                #                     7200000
                #                 ],
                #                 [
                #                     100000,
                #                     7100000
                #                 ]
                #             ]
                #         ]
                #     }
                # }

                # Start the Batch job for each cube with ROI != 0
                each_granule[CubeJson.PROPERTIES][CubeJson.DIRECTORY] = each_granule[CubeJson.PROPERTIES][CubeJson.DIRECTORY].replace(INPUT_FILE_PATH, OUTPUT_FILE_PATH)

            # Store updated catalog geojson to S3
            output_filename = os.path.join(S3_OUTPUT_PATH, os.path.basename(each))
            logging.info(f"Writing updated geojson to {output_filename}...")
            with s3_out.open(output_filename, 'w') as outf:
                json.dump(all_granules, outf)


if __name__ == '__main__':
    import argparse
    import warnings
    import sys
    warnings.filterwarnings('ignore')

    # Set up logging
    logging.basicConfig(
        level = logging.INFO,
        format = '%(asctime)s - %(levelname)s - %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S'
    )

    # Command-line arguments parser
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0],
                                     epilog=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    args = parser.parse_args()

    logging.info(f"Command-line arguments: {sys.argv}")

    rename_granule_paths()

    logging.info(f"Done")
