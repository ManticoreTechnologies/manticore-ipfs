# Manticore Technologies LLC
# (c) 2024 
# Manticore IPFS Mirror
#       routes.py 

from startup import app
from rpc import send_command
from utils import create_logger, config, load_map
from flask import send_file, abort
import os

@app.route('/ipfs/cid/<cid>', methods=['GET'])
def get_ipfs_content_bycid(cid):
    # Remove any extension from the requested CID (e.g., if the frontend requests cid.png)
    cid_base = os.path.splitext(cid)[0]
    
    # Search for the file with any extension
    directory = 'data/images'
    
    for filename in os.listdir(directory):
        # Compare the base name of the file
        if os.path.splitext(filename)[0] == cid_base:
            file_path = os.path.join(directory, filename)
            
            # If the file is a WebP image, serve it with a .png extension
            if filename.lower().endswith('.webp'):
                return send_file(file_path, mimetype='image/webp', download_name=f'{cid_base}.png')
            
            # Otherwise, send the file directly
            return send_file(file_path)
    
    # If the file is not found, return a 404 error
    abort(404, description=f"File for CID {cid_base} not found")

@app.route('/ipfs/name/<name>')
def get_ipfs_content_byname(name):
    by_name = load_map("by_name")
    try:
        return get_ipfs_content_bycid(by_name[name.upper()]['ipfs_hash'])
    except:
        return send_file("placeholder.png")