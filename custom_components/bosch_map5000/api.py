"""API Client for Bosch MAP5000 REST API."""
import asyncio
import hashlib
import logging
import ssl
from typing import Any, Dict, Optional
import re
from uuid import uuid4

import aiohttp

from .const import LOGGER

class MAP5000AuthError(Exception):
    """Exception for authentication errors."""

class MAP5000ConnectionError(Exception):
    """Exception for connection errors."""

class MAP5000Client:
    """Client for handling communication with MAP5000."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
        port: int = 443,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Initialize the API client."""
        self.host = host
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.port = port
        self.base_url = f"https://{self.host}:{self.port}"
        self._session = session or aiohttp.ClientSession()
        
        self._ssl_context = ssl.create_default_context()
        if not self.verify_ssl:
            self._ssl_context.check_hostname = False
            self._ssl_context.verify_mode = ssl.CERT_NONE
            
        self._nonce = ""
        self._realm = ""
        self._qop = ""
        self._nc = 0
        self._opaque = ""
        
        # Concurrency limit based on Bosch recommendations
        self._semaphore = asyncio.Semaphore(5)

    def _generate_digest_header(self, method: str, uri: str) -> str:
        """Generate Digest authentication header."""
        if not self._nonce:
            return ""

        self._nc += 1
        nc_str = f"{self._nc:08x}"
        cnonce = uuid4().hex

        # HA1 = MD5(username:realm:password)
        ha1 = hashlib.md5(f"{self.username}:{self._realm}:{self.password}".encode("utf-8")).hexdigest()
        
        # HA2 = MD5(method:digestURI)
        ha2 = hashlib.md5(f"{method}:{uri}".encode("utf-8")).hexdigest()

        # Response = MD5(HA1:nonce:nc:cnonce:qop:HA2)
        response_str = f"{ha1}:{self._nonce}:{nc_str}:{cnonce}:{self._qop}:{ha2}"
        response = hashlib.md5(response_str.encode("utf-8")).hexdigest()

        auth_parts = [
            f'username="{self.username}"',
            f'realm="{self._realm}"',
            f'nonce="{self._nonce}"',
            f'uri="{uri}"',
            f'cnonce="{cnonce}"',
            f'nc={nc_str}',
            f'qop="{self._qop}"',
            f'response="{response}"',
        ]
        
        if self._opaque:
            auth_parts.append(f'opaque="{self._opaque}"')

        return f"Digest {', '.join(auth_parts)}"

    def _parse_challenge(self, header: str) -> None:
        """Parse WWW-Authenticate header."""
        if not header.startswith("Digest "):
            return
            
        auth_str = header[7:]
        
        # Extract values using regex
        nonce_match = re.search(r'nonce="([^"]+)"', auth_str)
        realm_match = re.search(r'realm="([^"]+)"', auth_str)
        qop_match = re.search(r'qop="?([^",]+)"?', auth_str)
        opaque_match = re.search(r'opaque="([^"]+)"', auth_str)
        
        if nonce_match:
            self._nonce = nonce_match.group(1)
        if realm_match:
            self._realm = realm_match.group(1)
        if qop_match:
            self._qop = qop_match.group(1)
        if opaque_match:
            self._opaque = opaque_match.group(1)
            
        self._nc = 0

    async def request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the API."""
        url = f"{self.base_url}{endpoint}"
        
        async with self._semaphore:
            headers = {}
            if self._nonce:
                headers["Authorization"] = self._generate_digest_header(method, endpoint)
                
            if data:
                headers["Content-Type"] = "application/json"

            try:
                # First attempt
                response = await self._session.request(
                    method, 
                    url, 
                    headers=headers, 
                    json=data, 
                    ssl=self._ssl_context,
                    timeout=10
                )
                
                # If 401 Unauthorized, parse challenge and retry
                if response.status == 401:
                    auth_header = response.headers.get("WWW-Authenticate", "")
                    if "Digest" in auth_header:
                        self._parse_challenge(auth_header)
                        headers["Authorization"] = self._generate_digest_header(method, endpoint)
                        
                        # Consume previous response
                        await response.read()
                        
                        # Retry with new auth headers
                        response = await self._session.request(
                            method, 
                            url, 
                            headers=headers, 
                            json=data, 
                            ssl=self._ssl_context,
                            timeout=10
                        )
                
                if response.status == 401:
                    raise MAP5000AuthError("Authentication failed after digest challenge.")
                    
                response.raise_for_status()
                
                if response.status == 204 or response.content_length == 0:
                    return {}
                
                try:
                    return await response.json()
                except aiohttp.ContentTypeError:
                    text = await response.text()
                    LOGGER.debug("Response was not JSON: %s", text)
                    return {"raw": text}
                    
            except aiohttp.ClientError as err:
                raise MAP5000ConnectionError(f"Error communicating with MAP5000: {err}") from err

    async def get_description(self) -> Dict[str, Any]:
        """Get the system description."""
        return await self.request("GET", "/desc")

    async def get_areas(self) -> Dict[str, Any]:
        """Get all areas."""
        return await self.request("GET", "/areas")

    async def get_devices(self) -> Dict[str, Any]:
        """Get all devices."""
        return await self.request("GET", "/devices")
        
    async def get_incidents(self) -> Dict[str, Any]:
        """Get system incidents."""
        return await self.request("GET", "/inc")

    async def execute_command(self, endpoint: str, command: str) -> Dict[str, Any]:
        """Execute a specific command on an endpoint."""
        return await self.request("POST", endpoint, {"command": command})
