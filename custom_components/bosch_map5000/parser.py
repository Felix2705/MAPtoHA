import json
import logging
import os
import zipfile
from typing import Dict

from .const import LOGGER

def parse_map5000_zip(zip_path: str, password: str) -> Dict[str, str]:
    """
    Parse a password protected MAP5000 export zip file to extract
    plain text names mapped to their SIIDs.
    Returns a dictionary mapping SIID (with and without slashes) to name.
    """
    mapping = {}
    if not zip_path:
        return mapping

    if not os.path.exists(zip_path):
        LOGGER.error("MAP5000 ZIP file does not exist at path: %s", zip_path)
        return mapping

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            pwd = password.encode('utf-8') if password else None
            
            # Find the panel_cfg_compact.json file (case-insensitive)
            json_filename = None
            for name in zf.namelist():
                if name.lower().endswith("panel_cfg_compact.json"):
                    json_filename = name
                    break
                    
            if not json_filename:
                LOGGER.error("panel_cfg_compact.json not found in ZIP file: %s", zip_path)
                return mapping
                
            with zf.open(json_filename, pwd=pwd) as f:
                data = json.load(f)
                
            # Parse areaConfiguration
            for area in data.get("areaConfiguration", []):
                siid = area.get("siid")
                name = area.get("name")
                if siid and name:
                    clean_siid = siid.lstrip("/")
                    mapping[siid] = name
                    mapping[clean_siid] = name
                    mapping[f"/{clean_siid}"] = name
                    
            # Parse deviceConfiguration
            for device in data.get("deviceConfiguration", []):
                siid = device.get("siid")
                name = device.get("name")
                if siid and name:
                    clean_siid = siid.lstrip("/")
                    mapping[siid] = name
                    mapping[clean_siid] = name
                    mapping[f"/{clean_siid}"] = name
                    
            LOGGER.info("Successfully loaded %d name mappings from MAP5000 ZIP: %s", len(mapping), zip_path)
            
    except zipfile.BadZipFile:
        LOGGER.error("The file %s is not a valid ZIP archive", zip_path)
    except RuntimeError as e:
        if "password" in str(e).lower() or "bad password" in str(e).lower():
            LOGGER.error("Incorrect password for MAP5000 ZIP file: %s", zip_path)
        else:
            LOGGER.error("Error extracting MAP5000 ZIP file: %s", e)
    except Exception as e:
        LOGGER.error("Unexpected error parsing MAP5000 ZIP file: %s", e)
        
    return mapping
