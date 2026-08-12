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

def parse_xml_bytes(content: bytes, mapping: dict):
    """Extract SIIDs and Names from XML content into mapping dictionary."""
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
    except Exception as e:
        LOGGER.debug("Error parsing XML bytes: %s", e)

def parse_json_bytes(content: bytes, mapping: dict):
    """Extract SIIDs and Names from JSON content into mapping dictionary."""
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
    except Exception as e:
        LOGGER.debug("Error parsing JSON bytes: %s", e)

def resolve_file_path(file_path: str, base_config_dir: str = "") -> str:
    """Resolve user-entered file paths (handling /homeassistant/, /config/, relative paths)."""
    if not file_path:
        return ""

    # Normalize Samba / Home Assistant UI share prefixes
    cleaned = file_path
    if cleaned.startswith("/homeassistant/"):
        cleaned = cleaned.replace("/homeassistant/", "/config/", 1)
    elif cleaned.startswith("homeassistant/"):
        cleaned = cleaned.replace("homeassistant/", "/config/", 1)

    # Candidates to test
    candidates = [
        cleaned,
        os.path.normpath(cleaned),
    ]

    if base_config_dir:
        # If relative or starts with config
        rel = cleaned.lstrip("/")
        if rel.startswith("config/"):
            rel = rel.replace("config/", "", 1)
        candidates.append(os.path.join(base_config_dir, rel))
        candidates.append(os.path.join(base_config_dir, "custom_components", "bosch_map5000", os.path.basename(cleaned)))
        candidates.append(os.path.join(base_config_dir, os.path.basename(cleaned)))

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return os.path.abspath(candidate)

    # Return cleaned as fallback
    return cleaned

def parse_map5000_file(file_path: str, password: str = "", base_config_dir: str = "") -> Dict[str, str]:
    """
    Parse export files (.xml, .json, or .zip) to extract plain text names mapped to SIIDs.
    """
    mapping = {}
    resolved_path = resolve_file_path(file_path, base_config_dir)

    LOGGER.info("MAP5000 Name Parser: Input path='%s', Resolved path='%s'", file_path, resolved_path)

    if not os.path.exists(resolved_path):
        LOGGER.error("MAP5000 Name Parser: Export file does not exist at resolved path: %s", resolved_path)
        return mapping

    # 1. Direct XML file (or folder containing XML files)
    if resolved_path.lower().endswith(".xml"):
        dir_name = os.path.dirname(resolved_path)
        with open(resolved_path, "rb") as fp:
            parse_xml_bytes(fp.read(), mapping)

        # Parse all sibling XML files in the same folder to cover Areas (area_cfg_001.xml) + Devices (ld_all_cfg_001.xml)
        if dir_name and os.path.exists(dir_name):
            for sibling in os.listdir(dir_name):
                if sibling.lower().endswith(".xml") and os.path.join(dir_name, sibling) != resolved_path:
                    try:
                        with open(os.path.join(dir_name, sibling), "rb") as fp:
                            parse_xml_bytes(fp.read(), mapping)
                    except Exception:
                        pass
        LOGGER.info("MAP5000 Name Parser: Successfully loaded %d name mappings from XML files", len(mapping))
        return mapping

    # 2. Direct JSON file
    if resolved_path.lower().endswith(".json"):
        with open(resolved_path, "rb") as fp:
            parse_json_bytes(fp.read(), mapping)
        LOGGER.info("MAP5000 Name Parser: Successfully loaded %d name mappings from JSON file", len(mapping))
        return mapping

    # 3. ZIP archive
    if resolved_path.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(resolved_path, 'r') as zf:
                pwd = password.encode('utf-8') if password else None
                for name in zf.namelist():
                    if name.lower().endswith(".xml"):
                        try:
                            with zf.open(name, pwd=pwd) as fp:
                                parse_xml_bytes(fp.read(), mapping)
                        except Exception:
                            pass
                    elif name.lower().endswith("panel_cfg_compact.json"):
                        try:
                            with zf.open(name, pwd=pwd) as fp:
                                parse_json_bytes(fp.read(), mapping)
                        except Exception:
                            pass
            LOGGER.info("MAP5000 Name Parser: Successfully loaded %d name mappings from ZIP archive", len(mapping))
        except zipfile.BadZipFile:
            LOGGER.error("MAP5000 Name Parser: %s is not a valid ZIP archive", resolved_path)
        except RuntimeError as e:
            LOGGER.error("MAP5000 Name Parser: Incorrect password or extraction error for ZIP: %s", e)
        except Exception as e:
            LOGGER.error("MAP5000 Name Parser: Unexpected error reading ZIP: %s", e)
        return mapping

    return mapping

# Backward compatibility alias
parse_map5000_zip = parse_map5000_file
