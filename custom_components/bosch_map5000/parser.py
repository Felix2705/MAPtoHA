import json
import logging
import zipfile
from io import BytesIO
from typing import Dict, Optional

from .const import LOGGER

def parse_map5000_zip(zip_path: str, password: str) -> Dict[str, str]:
    """
    Parse a password protected MAP5000 export zip file to extract
    plain text names mapped to their SIIDs.
    Returns a dictionary mapping SIID to name.
    """
    mapping = {}
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            pwd = password.encode('utf-8')
            
            # Find the panel_cfg_compact.json file
            json_filename = None
            for name in zf.namelist():
                if name.endswith("panel_cfg_compact.json"):
                    json_filename = name
                    break
                    
            if not json_filename:
                LOGGER.error("panel_cfg_compact.json not found in ZIP file")
                return mapping
                
            with zf.open(json_filename, pwd=pwd) as f:
                data = json.load(f)
                
            # Parse areaConfiguration
            for area in data.get("areaConfiguration", []):
                siid = area.get("siid")
                name = area.get("name")
                if siid and name:
                    mapping[siid] = name
                    
            # Parse deviceConfiguration
            for device in data.get("deviceConfiguration", []):
                siid = device.get("siid")
                name = device.get("name")
                if siid and name:
                    mapping[siid] = name
                    
            LOGGER.info("Successfully loaded %d names from MAP5000 ZIP", len(mapping))
            
    except zipfile.BadZipFile:
        LOGGER.error("The provided file is not a valid ZIP file")
    except RuntimeError as e:
        if "password" in str(e).lower() or "bad password" in str(e).lower():
            LOGGER.error("Incorrect password for the MAP5000 ZIP file")
        else:
            LOGGER.error("Error extracting ZIP file: %s", e)
    except Exception as e:
        LOGGER.error("Unexpected error parsing MAP5000 ZIP file: %s", e)
        
    return mapping
