# Manticore Technologies LLC
# (c) 2024 
# Manticore IPFS Mirror
#       routes.py 

from startup import app
from rpc import send_command
from utils import create_logger, config, load_map
from flask import jsonify, request, send_file, abort
import time
import os


@app.route('/ipfs/cid/<cid>', methods=['GET'])
def get_ipfs_content_bycid(cid):
    # Construct the file path
    file_path = os.path.join('data', 'images', f'{cid}.png')
    
    # Check if the file exists
    if os.path.exists(file_path):
        # Send the file if it exists
        return send_file(file_path, mimetype='image/png')
    else:
        # Return a 404 error if the file is not found
        abort(404, description=f"File {cid}.png not found")

@app.route('/ipfs/name/<name>')
def get_ipfs_content_byname(name):
    by_name = load_map("by_name")
    return get_ipfs_content_bycid(by_name[name.upper()]['ipfs_hash'])

