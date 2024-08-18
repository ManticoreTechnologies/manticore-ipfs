# Manticore Technologies LLC
# (c) 2024 
# Manticore IPFS Mirror
#       utils.py 

import logging
import colorlog
import os

def create_logger():
    logger = logging.getLogger(os.path.basename(__file__))
    
    try:
        log_level = config['General']['log_level']
    except KeyError:
        raise KeyError("The 'log_level' setting is missing in the 'General' section of the configuration.")
    
    try:
        log_file = config['Logging']['log_file']
    except KeyError:
        raise KeyError("The 'log_file' setting is missing in the 'Logging' section of the configuration.")

    # Set the logging level
    logger.setLevel(log_level)

    # Clear existing handlers if any
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a stream handler with color formatting
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = colorlog.ColoredFormatter(
        fmt=(
            "%(log_color)s%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )
    
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # Create a file handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(log_level)
    logger.addHandler(fh)
    
    return logger
# Arguments #
import argparse

def parse_args():
    # Get the logging level argument
    parser = argparse.ArgumentParser(
        prog='Manticore Crypto Faucet',
        description='This cryptocurrency faucet is designed for Evrmore and Evrmore assets.',
        epilog='Manticore Technologies LLC'
    )
    parser.add_argument('--log-level', 
                        choices=['DEBUG', 'WARNING', 'CRITICAL', 'INFO', 'ERROR'], 
                        default='CRITICAL', 
                        help='Set the logging level (default: INFO)')

    return parser.parse_args()

# Settings #
import configparser
settings = configparser.ConfigParser()
settings.read('settings.conf')
config = configparser.ConfigParser()
config.read(settings['General']['config_path'])

# Welcome #
welcome_message =(
        "\n"
        "========================================\n"
        "         MANTICORE IPFS Mirror          \n"
        "========================================\n"
        "  (c) 2024 Manticore Technologies LLC   \n"
        "----------------------------------------\n"
        "Welcome to the Manticore IPFS Mirror! \n"
        "This mirror is designed for Evrmore assets.\n"
        "----------------------------------------\n"
)

# Cache #
import json
def initialize_directories():
    directories = ['./data/images', './data/maps']

    # Create directories if they don't exist
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Directory '{directory}' created.")
        else:
            print(f"Directory '{directory}' already exists.")



def save_maps(maps):
    """
    Saves the given maps to their respective file paths.

    Parameters:
    maps (list of tuples): A list where each tuple contains a map (dictionary) and the corresponding file path.
    """
    for map_data, file_path in maps:
        with open(file_path, 'w') as file:
            json.dump(map_data, file, indent=4)
            print(f"Saved map to {file_path}")

def load_maps(map_paths):
    """
    Loads the maps from the given file paths into memory.

    Parameters:
    map_paths (list of tuples): A list where each tuple contains a variable name and the corresponding file path.

    Returns:
    dict: A dictionary with variable names as keys and loaded maps as values.
    """
    loaded_maps = {}
    for map_name, file_path in map_paths:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                loaded_maps[map_name] = json.load(file)
                print(f"Loaded map '{map_name}' from {file_path}")
        else:
            print(f"File '{file_path}' does not exist. Map '{map_name}' not loaded.")
            loaded_maps[map_name] = {}
    return loaded_maps
def load_map(map_name):
    """
    Loads the maps from the given file paths into memory.

    Parameters:
    map_paths (list of tuples): A list where each tuple contains a variable name and the corresponding file path.

    Returns:
    dict: A dictionary with variable names as keys and loaded maps as values.
    """
    if os.path.exists(f"./data/maps/{map_name}.json"):
        with open(f"./data/maps/{map_name}.json", 'r') as file:
            return json.load(file)
    else:
        print(f"File '{map_name}' does not exist. Map '{map_name}' not loaded.")
        return {}

import requests
import time
from mimetypes import guess_extension
def download_image(ipfs_hash):
    print("ipfs_hash:", ipfs_hash)
    image_url = f"http://localhost:8080/ipfs/{ipfs_hash}"
    
    # Try downloading the image
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()
        
        # Determine the file extension based on the Content-Type header
        content_type = response.headers.get('Content-Type')
        if content_type:
            extension = guess_extension(content_type.split(';')[0].strip())
            if not extension:
                extension = ".bin"  # Default to binary if the extension cannot be guessed
        else:
            extension = ".bin"  # Default to binary if no content type is provided

        # Construct the full image path with the correct extension
        image_path = os.path.join(f"./data/images/{ipfs_hash}{extension}")

        # Return if already cached
        if os.path.exists(image_path):
            return

        # Save the image to the specified path
        with open(image_path, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)

        print(f"Downloaded image for IPFS hash {ipfs_hash} as {image_path}")
        time.sleep(0.3)
        return

    except (requests.RequestException, requests.Timeout) as e:
        print(f"Failed to download image for IPFS hash {ipfs_hash}. Saving placeholder.")
        
        # Save placeholder image data
        placeholder_path = "./placeholder.png"
        with open(placeholder_path, 'rb') as placeholder_file:
            placeholder_data = placeholder_file.read()
        
        # Save the placeholder image with a .png extension
        image_path = os.path.join(f"./data/images/{ipfs_hash}.png")
        with open(image_path, 'wb') as f:
            f.write(placeholder_data)
        
        return