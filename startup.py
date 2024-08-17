# Manticore Technologies LLC
# (c) 2024 
# Manticore IPFS Mirror
#       startup.py 

# Import utilities
from utils import create_logger, welcome_message, config, initialize_directories, save_maps
from PIL import Image  # Import Pillow for image validation
import os
import time
import mimetypes

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

def validate_and_correct_image(image_path):
    """
    Validate if the file is a valid image (PNG, GIF, etc.).
    If valid, check the file extension and correct it if necessary.
    If the file is invalid, delete it and return False.
    """
    try:
        logger.info(f"Validating image: {image_path}")
        with Image.open(image_path) as img:
            img.verify()  # Verify that it is an image
            img_format = img.format.lower()
            logger.info(f"Image format detected: {img_format}")

        # Determine the correct extension based on the image format
        correct_extension = f".{img_format}"
        current_extension = os.path.splitext(image_path)[1].lower()

        # Correct the file extension if necessary
        if current_extension != correct_extension:
            corrected_image_path = os.path.splitext(image_path)[0] + correct_extension
            os.rename(image_path, corrected_image_path)
            logger.info(f"Corrected file extension: {image_path} -> {corrected_image_path}")
            return corrected_image_path

        logger.info(f"Image validated and extension is correct: {image_path}")
        return image_path
    except (IOError, ValueError) as e:
        logger.error(f"Invalid or corrupt image file: {image_path}. Deleting it. Error: {e}")
        if os.path.exists(image_path):
            os.remove(image_path)
        return False

def cleanup_duplicates(directory):
    """
    Remove duplicate files with different extensions, keeping only the one with the correct extension.
    """
    logger.info("Starting duplicate cleanup")
    files_seen = {}
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        file_root, file_extension = os.path.splitext(file_path)
        
        if file_root in files_seen:
            existing_file = files_seen[file_root]
            correct_file = validate_and_correct_image(existing_file)
            
            if correct_file:
                logger.info(f"Deleting duplicate file: {file_path}")
                if os.path.exists(file_path):
                    os.remove(file_path)
            else:
                logger.info(f"Replacing incorrect file: {existing_file} with {file_path}")
                if os.path.exists(existing_file):
                    os.remove(existing_file)
                files_seen[file_root] = file_path
        else:
            corrected_file_path = validate_and_correct_image(file_path)
            if corrected_file_path:
                files_seen[file_root] = corrected_file_path

if __name__=="__main__":
    logger.info("Starting image downloader")
    
    from downloader import map_assets
    from utils import load_map, download_image
    from rpc import send_command

    # Initialize the necessary directories
    logger.info("Initializing necessary directories")
    existing_data = initialize_directories()

    # Clean up duplicates before downloading new images
    logger.info("Cleaning up duplicate files in the images directory")
    cleanup_duplicates("./data/images")

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
        
        # Reload the asset maps with latest data
        by_ipfshash = map_assets()[3]
        
        # Check if we have all the files saved
        for ipfs_hash in by_ipfshash:
            image_path = f"./data/images/{ipfs_hash}"
            cached = os.path.exists(image_path)
            if not cached:
                logger.info(f"Image not cached, downloading: {ipfs_hash}")
                # If we are missing one then try saving it
                download_image(ipfs_hash)
            
            # Validate and correct the image file extension
            if os.path.exists(image_path):
                result = validate_and_correct_image(image_path)
                if not result:
                    logger.warning(f"Deleted invalid image: {image_path}")
                elif isinstance(result, str):
                    # If the file extension was corrected, update the map or use the new path as needed
                    image_path = result
        
        # Sleep for a minute
        logger.info("Sleeping for 60 seconds")
        time.sleep(60)

else:
    logger.info("Let's start the flask app here since it's gunicorn")
    import routes
