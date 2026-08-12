import json
import logging
import os
import xml.etree.ElementTree as ET
import zipfile
from typing import Dict

from .const import LOGGER

def normalize_siid(siid: str) -> str:
    """Normalize SIID by removing leading zeros from numeric components."""
    if not siid:
        return ""
    siid_clean = siid.lstrip("/")
    parts = siid_clean.split(".")
    norm_parts = []
    for p in parts:
        if p.isdigit():
            norm_parts.append(str(int(p)))
        else:
            norm_parts.append(p)
    return ".".join(norm_parts)

def parse_map5000_file(file_path: str, password: str = "") -> Dict[str, str]:
    """
    Parse either a password protected ZIP file or an XML/JSON file directly
    to extract plain text names mapped to their normalized SIIDs.
    """
    mapping = {}
    if not file_path:
        return mapping

    if not os.path.exists(file_path):
        LOGGER.error("MAP5000 export file does not exist at path: %s", file_path)
        return mapping

    # If it's a direct XML file
    if file_path.lower().endswith(".xml"):
        return parse_xml_content(open(file_path, 'rb').read())

    # If it's a direct JSON file
    if file_path.lower().endswith(".json"):
        return parse_json_content(open(file_path, 'rb').read())

    # If it's a ZIP file
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            pwd = password.encode('utf-8') if password else None
            
            # 1. Search for ld_all_cfg_001.xml or any ld_*.xml file
            xml_filename = None
            for name in zf.namelist():
                if name.lower().endswith("ld_all_cfg_001.xml") or (name.lower().endswith(".xml") and "ld_" in name.lower()):
                    xml_filename = name
                    break

            if xml_filename:
                with zf.open(xml_filename, pwd=pwd) as f:
                    return parse_xml_content(f.read())

            # 2. Fallback to panel_cfg_compact.json
            json_filename = None
            for name in zf.namelist():
                if name.lower().endswith("panel_cfg_compact.json"):
                    json_filename = name
                    break

            if json_filename:
                with zf.open(json_filename, pwd=pwd) as f:
                    return parse_json_content(f.read())

            LOGGER.error("No valid XML or JSON configuration file found inside ZIP: %s", file_path)

    except zipfile.BadZipFile:
        LOGGER.error("The file %s is not a valid ZIP archive", file_path)
    except RuntimeError as e:
        if "password" in str(e).lower() or "bad password" in str(e).lower():
            LOGGER.error("Incorrect password for MAP5000 ZIP file: %s", file_path)
        else:
            LOGGER.error("Error extracting MAP5000 ZIP file: %s", e)
    except Exception as e:
        LOGGER.error("Unexpected error parsing MAP5000 export file: %s", e)

    return mapping

def parse_xml_content(content: bytes) -> Dict[str, str]:
    """Parse XML configuration content (ld_all_cfg_001.xml)."""
    mapping = {}
    try:
        root = ET.fromstring(content)
        for pkg in root.iter("Config_Package"):
            siid = pkg.attrib.get("SIID")
            name = pkg.attrib.get("Name")
            if siid and name:
                norm_siid = normalize_siid(siid)
                mapping[siid] = name
                mapping[norm_siid] = name
                mapping[f"/{norm_siid}"] = name
        LOGGER.info("Successfully loaded %d name mappings from XML", len(mapping))
    except Exception as e:
        LOGGER.error("Failed to parse XML content: %s", e)
    return mapping

def parse_json_content(content: bytes) -> Dict[str, str]:
    """Parse JSON configuration content (panel_cfg_compact.json)."""
    mapping = {}
    try:
        data = json.loads(content)
        for area in data.get("areaConfiguration", []):
            siid = area.get("siid")
            name = area.get("name")
            if siid and name:
                norm_siid = normalize_siid(siid)
                mapping[siid] = name
                mapping[norm_siid] = name
                mapping[f"/{norm_siid}"] = name

        for device in data.get("deviceConfiguration", []):
            siid = device.get("siid")
            name = device.get("name")
            if siid and name:
                norm_siid = normalize_siid(siid)
                mapping[siid] = name
                mapping[norm_siid] = name
                mapping[f"/{norm_siid}"] = name
        LOGGER.info("Successfully loaded %d name mappings from JSON", len(mapping))
    except Exception as e:
        LOGGER.error("Failed to parse JSON content: %s", e)
    return mapping

# Backward compatibility alias
parse_map5000_zip = parse_map5000_file
