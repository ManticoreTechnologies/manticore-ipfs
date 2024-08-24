# Import utilities
from utils import create_logger, welcome_message, config, initialize_directories, save_maps, load_map, download_image
import os
import time
import json

# Create a logger
logger = create_logger()

# Import flask
from flask import Flask

# Create flask application
app = Flask("Manticore IPFS Mirror")
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for testing purposes

# Log the welcome message
logger.info(welcome_message)

def cleanup_duplicates(directory):
    """
    Remove duplicate files with the same base name (ignoring extension), 
    keeping only one file.
    """
    logger.info("Starting duplicate cleanup")
    files_seen = {}

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        file_root, file_extension = os.path.splitext(file_path)

        # If the base file name has been seen before, delete the duplicate
        if file_root in files_seen:
            logger.info(f"Deleting duplicate file: {file_path}")
            os.remove(file_path)
        else:
            # Store the file as the "seen" file
            files_seen[file_root] = file_path

    logger.info("Duplicate cleanup complete")

def map_filetypes(directory):
    """
    Map the file extensions to a list of IPFS hashes for all files in the specified directory.
    """
    logger.info("Mapping file extensions to IPFS hashes in the directory")
    filetype_map = {}

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        file_root, file_extension = os.path.splitext(filename)

        if file_extension:
            # Ensure the file extension is lowercase and without the dot
            file_extension = file_extension.lstrip('.').lower()
            
            # Initialize the list for this file extension if it doesn't exist
            if file_extension not in filetype_map:
                filetype_map[file_extension] = []
            
            # Append the IPFS hash (base filename) to the list for this extension
            filetype_map[file_extension].append(file_root)
        else:
            # Handle files with no extension
            if 'unknown' not in filetype_map:
                filetype_map['unknown'] = []
            filetype_map['unknown'].append(file_root)

    # Save the file type map to a JSON file
    save_maps([(filetype_map, './data/maps/by_filetype.json')])

    logger.info("File extension to IPFS hash mapping complete")
    return filetype_map

def file_exists_base(directory, base_name):
    """
    Check if a file with the given base name exists in the directory, regardless of extension.
    """
    for filename in os.listdir(directory):
        if os.path.splitext(filename)[0] == base_name:
            return True
    return False

def retry_failed_downloads():
    """
    Retry downloading images for IPFS hashes listed in failed_downloads.json.
    """
    failed_downloads_path = './data/maps/failed_downloads.json'
    if os.path.exists(failed_downloads_path):
        with open(failed_downloads_path, 'r') as f:
            failed_downloads = json.load(f)
        
        # Remove duplicates from the failed downloads list
        failed_downloads = list(set(failed_downloads))
        
        logger.info(f"Retrying {len(failed_downloads)} failed downloads...")
        
        successful_retries = []
        for ipfs_hash in failed_downloads:
            logger.info(f"Retrying download for IPFS hash: {ipfs_hash}")
            download_image(ipfs_hash)
            # Check if download was successful
            if file_exists_base("./data/images", ipfs_hash):
                successful_retries.append(ipfs_hash)
        
        # Remove successfully retried IPFS hashes from failed_downloads.json
        remaining_failed_downloads = [hash for hash in failed_downloads if hash not in successful_retries]
        with open(failed_downloads_path, 'w') as f:
            json.dump(remaining_failed_downloads, f)
        
        logger.info(f"Retry complete. {len(remaining_failed_downloads)} downloads still failed.")
    else:
        logger.info("No failed downloads to retry.")

if __name__=="__main__":
    logger.info("Starting image downloader")
    
    from downloader import map_assets

    # Initialize the necessary directories
    logger.info("Initializing necessary directories")
    initialize_directories()

    # Clean up duplicates before downloading new images
    logger.info("Cleaning up duplicate files in the images directory")
    cleanup_duplicates("./data/images")

    # Map and save the file extensions to IPFS hashes in the images directory
    logger.info("Mapping file extensions to IPFS hashes")
    filetype_map = map_filetypes("./data/images")

    # Load the network assets by height
    logger.info("Loading network assets")
    by_name = load_map("by_name")
    by_ipfshash = load_map("by_ipfshash")
    
    # Initialize the maps if nothing was loaded
    if len(by_name) == 0 or len(by_ipfshash) == 0:
        logger.info("No data loaded, initializing maps")
        maps = map_assets()
        by_name = maps[0]
        by_ipfshash = maps[3]
    
    while True:
        logger.info("Updating asset maps")
        
        # Reload the asset maps with the latest data
        by_ipfshash = map_assets()[3]
        
        # Check if we have all the files saved
        for ipfs_hash in by_ipfshash:
            if not file_exists_base("./data/images", ipfs_hash):
                logger.info(f"Image not cached, downloading: {ipfs_hash}")
                # If we are missing one then try saving it
                download_image(ipfs_hash)
        
        # Retry failed downloads
        logger.info("Retrying failed downloads")
        retry_failed_downloads()
        
        # Sleep for a minute
        logger.info("Sleeping for 60 seconds")
        time.sleep(60)

else:
    logger.info("Let's start the flask app here since it's gunicorn")
    import routes
