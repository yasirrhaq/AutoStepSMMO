#!/usr/bin/env python3
"""
SimpleMMO Automation Bot
Developer testing tool for automating travel and adventure actions
"""

import requests
import time
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any, List, Tuple
import random
import re
from bs4 import BeautifulSoup
import sys
from io import BytesIO
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class SimpleMMOBot:
    """Bot for automating SimpleMMO travel and adventure actions"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize the bot with configuration"""
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.base_url = self.config.get("base_url", "https://web.simple-mmo.com")
        self.csrf_token = None
        self.api_token = None  # Separate API token for API calls
        self.logged_in = False
        
        # Setup session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Setup logging — use UTF-8 on the console handler so emoji never
        # raises UnicodeEncodeError on Windows cp1252 terminals.
        import sys as _sys
        _utf8_console = open(1, 'w', encoding='utf-8', errors='replace', closefd=False)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('simplemmo_bot.log', encoding='utf-8'),
                logging.StreamHandler(stream=_utf8_console),
            ]
        )
        self.logger = logging
        
        # Try to import PIL for CAPTCHA solving
        try:
            from PIL import Image
            self.has_pil = True
        except ImportError:
            self.has_pil = False
            self.logger.warning("PIL not available - CAPTCHA solving will be limited")
        
        # Configure pytesseract path for Windows if not in PATH
        try:
            import pytesseract
            import os
            if os.name == 'nt':  # Windows
                tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                if os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    self.logger.info(f"Configured Tesseract path: {tesseract_path}")
        except Exception as e:
            self.logger.warning(f"Could not configure Tesseract: {e}")
        
        # Smart model fallback tracking
        self.captcha_model_strategy = self.config.get("captcha_model_strategy", "smart_fallback")
        self.captcha_failure_threshold = self.config.get("captcha_failure_threshold", 5)
        self.base_model_failures = 0
        self.finetuned_model_failures = 0
        self.current_captcha_model = None  # Will be determined on first use
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_file} not found, using defaults")
            return {
                "base_url": "https://web.simple-mmo.com",
                "email": "",
                "password": "",
                "auto_travel": True,
                "travel_delay_min": 2,
                "travel_delay_max": 5,
                "enable_random_delays": True
            }
    
    def login(self, email: str = None, password: str = None, force_email_login: bool = False) -> bool:
        """Login to SimpleMMO"""
        # Check if session_token is provided in config (for OAuth users)
        session_token = self.config.get("session_token")
        xsrf_token = self.config.get("xsrf_token", "")
        
        # Try session token first (unless forced to use email/password)
        if session_token and not force_email_login:
            self.logger.info("Using session token from config...")
            success = self.login_with_session_token(session_token, xsrf_token)
            
            # If session token failed and we have email/password, try that as fallback
            if not success:
                email_conf = self.config.get("email")
                password_conf = self.config.get("password")
                if email_conf and password_conf:
                    self.logger.warning("Session token login failed")
                    self.logger.info("Waiting 3 seconds before fallback login...")
                    import time
                    time.sleep(3)  # Brief delay to avoid rate limiting
                    self.logger.info("Trying email/password login as fallback...")
                    return self.login_with_email_password(email_conf, password_conf)
            
            return success  # Return the session token login result
        
        # Fall back to email/password if session token didn't work
        email = email or self.config.get("email")
        password = password or self.config.get("password")
        
        if not email or not password:
            self.logger.error("Email and password (or session_token) required for login")
            return False
        
        return self.login_with_email_password(email, password)
    
    def login_with_email_password(self, email: str, password: str) -> bool:
        """Login using email and password"""
        login_url = f"{self.base_url}/login"
        
        try:
            # Clear any existing cookies that might interfere
            self.session.cookies.clear()
            self.logger.info("Cleared old cookies for fresh login")
            
            # Get login page and CSRF token
            self.logger.info("Fetching login page...")
            response = self.session.get(login_url)
            
            # Handle 403 specifically
            if response.status_code == 403:
                self.logger.error("HTTP 403 - Login page blocked")
                self.logger.error("Possible causes:")
                self.logger.error("  1. IP temporarily banned/rate limited")
                self.logger.error("  2. Too many failed login attempts")
                self.logger.error("  3. Cloudflare/WAF protection triggered")
                self.logger.error("")
                self.logger.error("Solutions:")
                self.logger.error("  - Wait 5-10 minutes before trying again")
                self.logger.error("  - Check if you can access the site in browser")
                self.logger.error("  - Try from a different network/VPN")
                self.logger.error("  - Use session token instead (see SESSION_TOKEN_GUIDE.md)")
                return False
            
            response.raise_for_status()
            
            # Extract CSRF token
            csrf_token = self._extract_csrf_token(response.text)
            if not csrf_token:
                self.logger.error("Failed to extract CSRF token")
                return False
            
            self.logger.info("Submitting login credentials...")
            
            # Perform login
            login_data = {
                'email': email,
                'password': password,
                '_token': csrf_token
            }
            
            response = self.session.post(login_url, data=login_data, allow_redirects=True)
            
            # Check if login was successful by looking for typical logged-in indicators
            if response.status_code == 200:
                # Check if we're redirected to home/dashboard or still on login page
                if 'login' not in response.url.lower() or 'Logout' in response.text or 'Travel' in response.text:
                    self.logged_in = True
                    self.csrf_token = self._extract_csrf_token(response.text)
                    
                    # Extract API token
                    self._extract_api_token(response.text)
                    if not self.api_token and self.config.get("api_token"):
                        self.api_token = self.config.get("api_token")
                        self.logger.info("Using api_token from config.json")
                    
                    self.logger.info("Successfully logged in with email/password")
                    return True
            
            self.logger.error("Login failed - check credentials")
            return False
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False
    
    def login_with_session_token(self, session_token: str, xsrf_token: str = "") -> bool:
        """Login using session token/cookie (for OAuth users like Google login)"""
        try:
            self.logger.info("Logging in with session token...")
            
            # URL-decode the tokens if they appear to be encoded
            if '%' in session_token:
                from urllib.parse import unquote
                session_token_decoded = unquote(session_token)
                self.logger.info("Session token was URL-encoded, decoded it")
            else:
                session_token_decoded = session_token
            
            if xsrf_token and '%' in xsrf_token:
                from urllib.parse import unquote
                xsrf_token = unquote(xsrf_token)
                self.logger.info("XSRF token was URL-encoded, decoded it")
            
            # Set cookies for multiple domain variations to work across web. and api. subdomains
            for domain in ['.simple-mmo.com', 'web.simple-mmo.com', 'api.simple-mmo.com', 'simple-mmo.com']:
                # Set laravel session cookie
                self.session.cookies.set(
                    'laravelsession',
                    session_token_decoded,
                    domain=domain,
                    path='/',
                    secure=True
                )
                
                # Set XSRF token if provided
                if xsrf_token:
                    self.session.cookies.set(
                        'XSRF-TOKEN',
                        xsrf_token,
                        domain=domain,
                        path='/',
                        secure=True
                    )
                    # Also set as header
                    self.session.headers.update({'X-XSRF-TOKEN': xsrf_token})
            
            # Set additional headers to look more like a real browser
            self.session.headers.update({
                'Referer': f'{self.base_url}/',
                'Origin': self.base_url
            })
            
            # Try to access a protected page to verify the session
            self.logger.info("Verifying session token...")
            response = self.session.get(f"{self.base_url}/travel", allow_redirects=True)
            
            self.logger.info(f"Response URL: {response.url}")
            self.logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                if 'login' not in response.url.lower():
                    # In Laravel, the XSRF-TOKEN cookie IS the CSRF token
                    if xsrf_token:
                        self.csrf_token = xsrf_token
                        self.logger.info("Using XSRF-TOKEN as CSRF token")
                        
                        # Extract API token from the page
                        self._extract_api_token(response.text)
                        
                        # If not found, try to get from config
                        if not self.api_token and self.config.get("api_token"):
                            self.api_token = self.config.get("api_token")
                            self.logger.info("Using api_token from config.json")
                    else:
                        # Try to extract CSRF token from HTML if no XSRF token provided
                        self.csrf_token = self._extract_csrf_token(response.text)
                    
                    if self.csrf_token:
                        self.logged_in = True
                        self.logger.info("Successfully logged in with session token")
                        return True
                    else:
                        self.logger.warning("Logged in but no CSRF token available")
                        self.logged_in = True
                        return True
                else:
                    self.logger.error(f"Session rejected - redirected to login page")
                    self.logger.error("Your session token may be expired. Please get a fresh one from your browser.")
                    self.logger.info("See SESSION_TOKEN_GUIDE.md for instructions")
                    return False
            elif response.status_code == 403:
                self.logger.error("HTTP 403 Forbidden - Session token rejected")
                self.logger.error("This could mean:")
                self.logger.error("  1. Session token expired")
                self.logger.error("  2. XSRF token missing or invalid")
                self.logger.error("  3. IP temporarily blocked")
                self.logger.info("Bot will try email/password fallback if configured...")
                return False
            else:
                self.logger.error(f"Failed to access protected page: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Session login error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def update_csrf_token(self, url: str = None) -> bool:
        """Update CSRF token from a page"""
        try:
            url = url or f"{self.base_url}/travel"
            response = self.session.get(url)
            if response.status_code == 200:
                token = self._extract_csrf_token(response.text)
                if token:
                    self.csrf_token = token
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update CSRF token: {e}")
            return False
    
    def _extract_csrf_token(self, html: str) -> str:
        """Extract CSRF token from HTML"""
        # Try multiple patterns to find CSRF token
        patterns = [
            r'<meta[^>]+name=["\']csrf-token["\'][^>]+content=["\']([^"\'\n]+)["\']',
            r'<input[^>]+name=["\']_token["\'][^>]+value=["\']([^"\'\n]+)["\']',
            r'"csrf-token"[^>]*>([^<]+)<',
            r'csrf_token["\']\\s*:\\s*["\']([^"\'\n]+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                token = match.group(1).strip()
                if token:
                    return token
        
        # Try with BeautifulSoup as fallback
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Check meta tag
            meta = soup.find('meta', {'name': 'csrf-token'})
            if meta and meta.get('content'):
                return meta.get('content')
            # Check hidden input
            input_tag = soup.find('input', {'name': '_token'})
            if input_tag and input_tag.get('value'):
                return input_tag.get('value')
        except:
            pass
        
        return ""
    
    def _extract_api_token(self, html: str) -> bool:
        """Extract API token from page (different from CSRF token)"""
        # Look for api_token in JavaScript or data attributes
        patterns = [
            r'api_token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'data-api-token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'window\.api_token\s*=\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                self.api_token = match.group(1)
                self.logger.info(f"Extracted API token (length: {len(self.api_token)})")
                return True
        
        self.logger.warning("Could not extract API token from page")
        return False
    
    def _parse_travel_response(self, html: str) -> Dict[str, Any]:
        """Parse travel response for items, gold, encounters, etc."""
        result = {
            "message": "",
            "items": [],
            "gold": None,
            "experience": None,
            "encounter": None
        }
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for battle results, items found, etc.
            # This will depend on actual HTML structure
            # Placeholder for now - adjust based on actual response
            
            # Try to find the main message/result text
            main_text = soup.get_text()
            if "You take a step" in main_text:
                result["message"] = "Travel step completed"
            
            return result
        except:
            return result
    
    def get_random_delay(self, min_delay: float, max_delay: float) -> float:
        """Get random delay if enabled, otherwise return min delay"""
        if self.config.get("enable_random_delays", True):
            return random.uniform(min_delay, max_delay)
        return min_delay
    
    def _parse_travel_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse travel API response to extract exp, gold, items, etc."""
        results = {
            "exp": 0,
            "gold": 0,
            "items": [],
            "message": "",
            "step_count": 0,
            "captcha": False,
            "wait_time": 0,
            "npc_encounter": False,
            "npc_id": None,
            "npc_name": None,
            "current_gold": 0,
            "current_exp": 0,
            "material_encounter": False,
            "material_session_id": None,
            "material_quantity": 0,
            "material_name": None,
            "material_img_src": None,
            "material_gather_url": None,
        }
        
        try:
            # Parse based on actual API response structure
            if isinstance(data, dict):
                # Get the main text/message
                text = data.get("text", "")
                results["message"] = text
                
                # SimpleMMO uses a 'type' field to signal what happened this step.
                # However 'type' and 'rewardType' are often 'none' even for real encounters.
                # 'step_type' is a more reliable field that actually says 'npc', 'material', etc.
                _type_candidates = [
                    str(data.get("step_type") or ""),
                    str(data.get("type") or ""),
                    str(data.get("rewardType") or ""),
                ]
                step_type = next(
                    (t.lower() for t in _type_candidates
                     if t.lower() not in ("", "none", "normal")),
                    "none"
                )

                # ── KEY FIELD: 'value' carries the ID for NPC/material steps ────
                # e.g. {"type": "npc", "value": 1234}  or  {"type": "material", "value": 5678}
                raw_value = data.get("value")

                # Always log the full raw JSON (helps identify actual field names)
                import json as _json
                import re as _img_re
                # Show full text when it contains HTML (NPC/material encounters embed HTML in text field)
                _text_has_html = "<img" in str(text) or "<span" in str(text) or "<div" in str(text)
                _txt_preview = str(text) if (step_type == "item" or _text_has_html) else str(text)[:120]
                _text_is_img = str(text).strip().startswith("<img")
                if self.config.get("debug_mode", False):
                    self.logger.info(f"[RAW TRAVEL] type={step_type!r} value={raw_value!r} text={_txt_preview!r}")
                    # Full JSON only in debug mode
                    if step_type not in ("", "gold", "exp", "experience", "none", "normal", "item") or _text_has_html:
                        self.logger.info(f"[RAW TRAVEL FULL] {_json.dumps(data)}")

                # Check for CAPTCHA challenge
                if "i-am-not-a-bot" in text.lower() or "hold up" in text.lower():
                    results["captcha"] = True
                    return results

                # ── NPC encounter detection ──────────────────────────────────
                # Priority 1: explicit 'type' field from API
                npc_from_type = step_type in ("npc", "battle", "enemy", "encounter", "pvp", "monster")

                # Priority 2: explicit npc_id field OR the generic 'value' field when type==npc
                npc_id = (
                    data.get("npc_id") or data.get("npcId") or data.get("encounter_npc_id")
                    or (raw_value if npc_from_type and raw_value else None)
                )
                npc_name = data.get("npc_name") or data.get("npcName") or data.get("encounter_npc_name")

                # Priority 3: nested npc object
                npc_data = data.get("npc") or data.get("encounter") or data.get("battle")
                if isinstance(npc_data, dict):
                    npc_id = npc_id or npc_data.get("id") or npc_data.get("npc_id")
                    npc_name = npc_name or npc_data.get("name") or npc_data.get("npc_name")

                # Priority 4: text HTML contains an avatar <img> — event NPC encounter
                # e.g. text = "<img src='/img/sprites/events/lunar-new-year-26/avatars/lantern_sage.png'>..."
                if not npc_id and _text_has_html:
                    _text_str = str(text)
                    # Avatar image = NPC encounter
                    _av_m = _img_re.search(r"src=['\"]([^'\"]*?/avatars/[^'\"]+)", _text_str)
                    if _av_m:
                        # Try to extract NPC ID from text HTML (onclick, data attr, href, numeric id)
                        _npc_id_pats = [
                            r"attackNpc\((\d+)\)",
                            r"attack_npc\((\d+)\)",
                            r"npc[_-]?id[^\d]{0,10}(\d+)",
                            r"data-npc[^=]*=['\"]?(\d+)",
                            r"npcs/attack/(\d+)",
                            r"battle.{0,20}npc.{0,20}(\d{3,})",
                            r"/(npcs|npc)/view/(\d+)",
                        ]
                        for _p in _npc_id_pats:
                            _pm = _img_re.search(_p, _text_str, _img_re.IGNORECASE)
                            if _pm:
                                npc_id = int(_pm.group(_pm.lastindex))
                                break
                        # Also try raw_value as fallback
                        if not npc_id and raw_value:
                            npc_id = raw_value
                        # Extract NPC name from img src filename
                        _av_fname = _av_m.group(1).rstrip("/").split("/")[-1]
                        _av_fname = _img_re.sub(r'\.(gif|png|jpg|jpeg|webp)$', '', _av_fname, flags=_img_re.IGNORECASE)
                        npc_name = npc_name or _av_fname.replace("_", " ").replace("-", " ").title()
                        npc_from_type = True  # treat as a confirmed NPC encounter
                        self.logger.info(
                            f"[NPC IMG DETECT] name={npc_name!r} id={npc_id!r} "
                            f"src={_av_m.group(1)!r}"
                        )

                # Only flag as NPC encounter if we have concrete evidence
                if npc_from_type or npc_id:
                    results["npc_encounter"] = True
                    results["npc_id"] = npc_id
                    results["npc_name"] = npc_name

                # ── Material/gathering encounter detection ───────────────────
                # Priority 1: explicit 'type' field from API
                material_from_type = step_type in (
                    "material", "gather", "gathering", "salvage",
                    "materialgather", "material_gather"
                )

                # Priority 2: session ID field — try every known name variant
                # ALSO check the 'value' field when type indicates material
                nested = data.get("data", {})
                nested = nested if isinstance(nested, dict) else {}
                material_session_id = (
                    data.get("material_session_id") or data.get("materialSessionId")
                    or data.get("gathering_session_id") or data.get("gatheringSessionId")
                    or data.get("session_id")
                    or nested.get("material_session_id") or nested.get("materialSessionId")
                    or nested.get("gathering_session_id") or nested.get("session_id")
                    or (raw_value if material_from_type and raw_value else None)
                )
                # Also scan the text HTML for 'material_session_id: 12345'
                # (SMMO embeds it in the Grab button's x-on:click attribute)
                if not material_session_id and text:
                    _tsid = _img_re.search(r'material_session_id["\']?\s*[:\s,]+\s*(\d+)', str(text))
                    if _tsid:
                        material_session_id = int(_tsid.group(1))
                        self.logger.info(f"[MATERIAL SESSION from text] id={material_session_id}")

                # Priority 3: text keywords
                has_material_keywords = False
                if text:
                    text_lower = text.lower()
                    material_phrases = [
                        "material found", "salvage material", "gather material",
                        "gathering material", "you found material", "discovered material",
                        "material discovered", "you found some", "material awaits"
                    ]
                    has_material_keywords = any(phrase in text_lower for phrase in material_phrases)

                # Priority 4: text IS an <img> tag pointing to a material/event sprite
                # e.g. text = "<img src='/img/sprites/events/.../emperors_fireworks.gif'>"
                _text_is_img_material = False
                _img_mat_name = None
                _img_mat_session = None
                if _text_is_img:  # set above near the logging block
                    _src_m = _img_re.search(r"src=['\"]([^'\"]+)['\"]", text)
                    if _src_m:
                        _src = _src_m.group(1)
                        # /avatars/ = NPC encounter, NOT a material — exclude it
                        _is_avatar = "/avatars/" in _src
                        if not _is_avatar and ("materials/" in _src or "/events/" in _src or "/sprites/" in _src):
                            _text_is_img_material = True
                            # Derive a human-readable name from the filename (e.g. "Emperors Fireworks")
                            _fname = _src.rstrip("/").split("/")[-1]
                            _fname = _img_re.sub(r'\.(gif|png|jpg|jpeg|webp)$', '', _fname, flags=_img_re.IGNORECASE)
                            _img_mat_name = _fname.replace("_", " ").replace("-", " ").title()
                            # raw_value is very likely the gathering session_id for these steps
                            _img_mat_session = raw_value if raw_value else None
                            # Also scan text HTML directly for embedded session ID
                            if not _img_mat_session:
                                _tsid2 = _img_re.search(
                                    r'material_session_id["\']?\s*[:\s,]+\s*(\d+)', str(text)
                                )
                                if _tsid2:
                                    _img_mat_session = int(_tsid2.group(1))
                            self.logger.info(
                                f"[MATERIAL IMG DETECT] name={_img_mat_name!r} "
                                f"candidate_session_id={_img_mat_session!r} src={_src!r}"
                            )

                if material_from_type or material_session_id:
                    # Strong signal (type field or session ID) — always act
                    results["material_encounter"] = True
                    results["material_session_id"] = material_session_id
                    results["material_quantity"] = data.get("quantity", data.get("amount",
                        nested.get("quantity", nested.get("amount", 1))))
                    results["material_name"] = (
                        data.get("material_name") or data.get("materialName")
                        or data.get("name") or nested.get("name")
                    )
                elif _text_is_img_material:
                    # Event/material <img> in text field — set encounter and use raw_value as session_id
                    results["material_encounter"] = True
                    results["material_session_id"] = _img_mat_session
                    results["material_quantity"] = data.get("quantity", data.get("amount", 1))
                    results["material_name"] = _img_mat_name
                    results["material_img_src"] = _src_m.group(1) if _src_m else None
                elif has_material_keywords:
                    # Weak signal (text only) — flag but do NOT set a name derived from
                    # generic fields (avoids the 'Material' false positive)
                    results["material_encounter"] = True
                    results["material_session_id"] = None  # will be resolved from page HTML
                    results["material_quantity"] = data.get("quantity", data.get("amount", 1))
                    results["material_name"] = data.get("material_name") or data.get("materialName")

                # ── Scan ALL string values in the response for a signed gather URL ──
                # SMMO sometimes embeds the gather URL directly in the travel API JSON,
                # especially for event materials (e.g. Lunar New Year fireworks)
                if results["material_encounter"] and not results.get("material_gather_url"):
                    _SIGNED_PAT = _img_re.compile(
                        r'https?://[^\s\'"]+/gathering/material/gather\?expires=\d+[^\s\'"]*',
                        _img_re.IGNORECASE
                    )
                    def _scan_for_gather_url(obj, depth=0):
                        if depth > 5:
                            return None
                        if isinstance(obj, str):
                            m = _SIGNED_PAT.search(obj)
                            if m:
                                return m.group(0).replace("\\u0026", "&").replace("\\/", "/")
                        elif isinstance(obj, dict):
                            for v in obj.values():
                                r = _scan_for_gather_url(v, depth + 1)
                                if r:
                                    return r
                        elif isinstance(obj, list):
                            for v in obj:
                                r = _scan_for_gather_url(v, depth + 1)
                                if r:
                                    return r
                        return None
                    _found_gather_url = _scan_for_gather_url(data)
                    if _found_gather_url:
                        results["material_gather_url"] = _found_gather_url
                        self.logger.info(f"[MATERIAL GATHER URL from API] {_found_gather_url!r}")

                # ── Item drop (type='item') — parse name and rarity from HTML text ──
                if step_type == "item" and text:
                    import re as _re

                    _rarity_map = {
                        "common": "Common", "uncommon": "Uncommon", "rare": "Rare",
                        "elite": "Elite", "epic": "Epic", "legendary": "Legendary",
                        "mythic": "Mythic", "celestial": "Celestial",
                    }

                    # ── Rarity from CSS class ────────────────────────────────
                    _rarity = "Common"
                    _rc = _re.search(
                        r"class=['\"][^'\"]*\b(common|uncommon|rare|elite|epic|legendary|mythic|celestial)\b[^'\"]*['\"]",
                        text, _re.I
                    )
                    if _rc:
                        _rarity = _rarity_map.get(_rc.group(1).lower(), "Common")

                    # ── Item name — 5 strategies, first match wins ───────────
                    _name = None

                    # 1. Anchor tag INSIDE the rarity-class span
                    #    <span class='rare-item' ...><a href="...">Sword of Doom</a></span>
                    if not _name:
                        _m = _re.search(
                            r"class=['\"][^'\"]*(?:common|uncommon|rare|elite|epic|legendary|mythic|celestial)[^'\"]*['\"][^>]*>[^<]*<a[^>]*>([^<]{2,60})</a>",
                            text, _re.I
                        )
                        if _m:
                            _name = _m.group(1).strip()

                    # 2. Direct span text (no nested tag)
                    #    <span class='common-item' ...>Iron Ball</span>
                    if not _name:
                        _m = _re.search(
                            r"class=['\"][^'\"]*(?:common|uncommon|rare|elite|epic|legendary|mythic|celestial)[^'\"]*['\"][^>]*>([^<]{2,60})</span>",
                            text, _re.I
                        )
                        if _m:
                            _name = _m.group(1).strip()

                    # 3. Any anchor whose href contains /item(s)/ or /equipment/
                    #    <a href="/items/1234">Iron Ball</a>
                    if not _name:
                        _m = _re.search(
                            r"<a[^>]*href=['\"][^'\"]*(?:/items?/|/equipment/|/weapon/|/armou?r/)[^'\"]*['\"][^>]*>([^<]{2,60})</a>",
                            text, _re.I
                        )
                        if _m:
                            _name = _m.group(1).strip()

                    # 4. Any anchor link text that looks like a proper noun
                    if not _name:
                        _m = _re.search(r"<a[^>]+>([A-Z][a-zA-Z0-9 '\-]{2,50})</a>", text)
                        if _m:
                            _name = _m.group(1).strip()

                    # 5. Derive name from img src filename
                    #    /img/icons/I_IronBall.png  ->  Iron Ball
                    #    /img/icons/midnight/armour/Helmet1.png  ->  Helmet 1
                    if not _name:
                        _im = _re.search(r"/([^/]+)\.png", text, _re.I)
                        if _im:
                            _raw = _im.group(1)
                            _raw = _re.sub(r'^[Ii][_-]', '', _raw)          # strip I_ prefix
                            _raw = _re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', _raw)  # CamelCase split
                            _raw = _re.sub(r'(?<=[A-Z]{2})(?=[A-Z][a-z])', ' ', _raw)  # ABCDef -> ABC Def
                            _raw = _re.sub(r'([0-9]+)', r' \1', _raw)      # digits get a space
                            _raw = _re.sub(r'[_-]', ' ', _raw)              # underscores -> spaces
                            _raw = _re.sub(r'  +', ' ', _raw).strip()
                            if _raw and len(_raw) >= 2:
                                _name = _raw

                    if not _name:
                        _name = "Unknown Item"

                    # Only populate if not already filled from structured API data
                    if not results["items"]:
                        results["items"].append({"name": _name, "rarity": _rarity, "quantity": 1})

                # Get reward info - PRIMARY reward fields
                reward_type = data.get("rewardType", "none")
                reward_amount = data.get("rewardAmount", 0)
                result_text = data.get("resultText", "none")
                
                # Parse rewards based on type
                if reward_type in ["gold", "coins", "money", "currency"]:
                    results["gold"] = reward_amount
                elif reward_type in ["exp", "experience", "xp", "experiance"]:  # Note: API might have typo
                    results["exp"] = reward_amount
                elif reward_type == "item":
                    # Item info might be in text or separate field
                    item_data = data.get("item", {})
                    if item_data:
                        results["items"].append(item_data)
                
                # Parse ADDITIONAL common fields (add to existing, not replace)
                # Check for gold_amount and exp_amount first (primary fields in API)
                results["gold"] += data.get("gold_amount", 0)
                results["exp"] += data.get("exp_amount", 0)
                
                # Also check alternative field names
                results["exp"] += data.get("exp", data.get("experience", data.get("xp", data.get("experiance", 0))))
                results["gold"] += data.get("gold", data.get("coins", data.get("money", data.get("currency", 0))))
                
                # Try to parse gold/exp from result text if not found yet
                if results["gold"] == 0 and result_text != "none":
                    # Look for patterns like "gold: 50" or "50 gold"
                    import re
                    gold_match = re.search(r'(\d+)\s*gold|gold[:\s]+(\d+)', result_text.lower())
                    if gold_match:
                        gold_val = gold_match.group(1) or gold_match.group(2)
                        results["gold"] = int(gold_val)
                
                if results["exp"] == 0 and result_text != "none":
                    # Look for patterns like "exp: 100" or "100 exp"
                    import re
                    exp_match = re.search(r'(\d+)\s*exp|exp[:\s]+(\d+)', result_text.lower())
                    if exp_match:
                        exp_val = exp_match.group(1) or exp_match.group(2)
                        results["exp"] = int(exp_val)
                
                # Items can be in various formats
                items = data.get("items", data.get("loot", data.get("rewards", data.get("inventory", []))))
                if isinstance(items, list):
                    results["items"].extend(items)
                elif isinstance(items, dict) and items:
                    results["items"].append(items)
                
                # Get wait time (cooldown)
                wait_length = data.get("wait_length", data.get("waitLength", data.get("cooldown", 0)))
                if wait_length:
                    results["wait_time"] = wait_length / 1000  # Convert ms to seconds
                
                # Step count
                results["step_count"] = data.get("steps", data.get("step_count", data.get("stepCount", 0)))
                
                # Current totals from API
                results["current_gold"] = data.get("currentGold", data.get("current_gold", data.get("total_gold", 0)))
                results["current_exp"] = data.get("currentEXP", data.get("current_exp", data.get("total_exp", 0)))
                
                # Store raw data for debugging
                results["raw"] = data
                
                # Debug logging if we got unexpected structure
                if results["gold"] == 0 and results["exp"] == 0 and not results["items"] and not results["material_encounter"]:
                    self.logger.debug(f"No rewards parsed from: {data}")
                    
        except Exception as e:
            self.logger.warning(f"Error parsing travel results: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
        
        return results

    # ── Gathering helpers ────────────────────────────────────────────────────

    def _fetch_html(self, url: str, **kwargs) -> str:
        """
        GET a URL and return the response body as a decoded string.

        Handles gzip-compressed responses that the requests session may not
        automatically decompress (e.g. when a custom Accept header or session
        adapter interferes with Content-Encoding negotiation).
        """
        import gzip as _gzip
        kwargs.setdefault("allow_redirects", True)
        kwargs.setdefault("timeout", 10)
        # Force server to return identity (uncompressed) content.
        # If server ignores this, fall back to manual decompression below.
        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept-Encoding", "identity")
        resp = self.session.get(url, headers=headers, **kwargs)
        raw = resp.content
        if raw[:2] == b'\x1f\x8b':
            try:
                return _gzip.decompress(raw).decode("utf-8", errors="replace")
            except Exception:
                pass
        return resp.text

    def _extract_gathering_urls(self, html: str) -> dict:
        """
        Extract the signed gathering API URLs and session ID from a travel page.

        SimpleMMO embeds signed URLs in the page HTML (same \\/\\ JSON-escape
        pattern as NPC attack URLs).  Three attempts per URL:
          1. Plain absolute URL
          2. JSON-escaped (backslash-slashes + \\u0026 ampersand)
          3. Relative path with query-string components

        Returns dict: {session_id, info_url, gather_url} — all may be None.
        """
        import re as _re
        result = {"session_id": None, "info_url": None, "gather_url": None}

        # ── Session ID ──────────────────────────────────────────────────────
        for pat in [
            r'material_session_id[\s\'"]*:\s*(\d+)',      # JS/x-data: key: value
            r'material_session_id\D{0,15}?(\d+)',
            r'materialSessionId\D{0,15}?(\d+)',
            r'gathering_session_id\D{0,15}?(\d+)',
            r'gatheringSessionId\D{0,15}?(\d+)',
            r'"id"\s*:\s*(\d{7,})',                        # numeric id ≥ 7 digits
        ]:
            m = _re.search(pat, html, _re.IGNORECASE)
            if m:
                result["session_id"] = int(m.group(m.lastindex))
                break

        WB = self.base_url  # https://web.simple-mmo.com
        AB = "https://api.simple-mmo.com"

        # ── Helper to build URL from multiple match patterns ─────────────────
        def _find_url(endpoint: str) -> str | None:
            ep_esc = endpoint.replace("/", "\\/")
            # Pattern 1: plain absolute URL (web or api domain)
            for base in (WB, AB):
                m = _re.search(
                    rf'({re.escape(base)}/{re.escape(endpoint)}'
                    rf'\?expires=\d+&(?:amp;)?signature=[a-f0-9]+)',
                    html,
                )
                if m:
                    return m.group(1).replace("&amp;", "&")
            # Pattern 2: JSON-escaped single backslash (web or api)
            for base_esc in ("web\\.simple-mmo\\.com", "api\\.simple-mmo\\.com"):
                m = _re.search(
                    rf'https:\\/\\/{base_esc}\\/{ep_esc}'
                    rf'\?expires=(\d+)(?:\\u0026|&(?:amp;)?)signature=([a-f0-9]+)',
                    html,
                )
                if m:
                    return f"{WB}/{endpoint}?expires={m.group(1)}&signature={m.group(2)}"
            # Pattern 3: relative path with query string
            seg = endpoint.split("/")[-1]  # e.g. "gather" or "information"
            m = _re.search(
                rf'gathering/material/{_re.escape(seg)}[^?]*\?expires=(\d+)&(?:amp;)?signature=([a-f0-9]+)',
                html,
            )
            if m:
                return f"{WB}/api/gathering/material/{seg}?expires={m.group(1)}&signature={m.group(2)}"
            # Pattern 4: Livewire wire:snapshot double-encoded (\\\\/ = \\\/ in HTML)
            m = _re.search(
                rf'gathering\\\\/material\\\\/{_re.escape(seg)}'
                rf'[^?"\']*\?expires=(\d+)(?:\\\\u0026|&)signature=([a-f0-9]+)',
                html,
            )
            if m:
                return f"{WB}/api/gathering/material/{seg}?expires={m.group(1)}&signature={m.group(2)}"
            # Pattern 5: broad fallback — any URL fragment containing the segment + expires + signature
            m = _re.search(
                rf'["\']([^"\']*gathering[/\\\\]+material[/\\\\]+{_re.escape(seg)}'
                rf'[^"\']*expires=(\d+)[^"\']*signature=([a-f0-9]+)[^"\']*)["\']',
                html,
            )
            if m:
                raw = m.group(1).replace("\\/", "/").replace("\\u0026", "&").replace("\\\\", "")
                if not raw.startswith("http"):
                    raw = f"{WB}/{raw.lstrip('/')}"
                return raw
            return None

        result["info_url"]   = _find_url("api/gathering/material/information")
        result["gather_url"] = _find_url("api/gathering/material/gather")

        _log_fn = self.logger.info if (result["session_id"] or result["info_url"] or result["gather_url"]) else self.logger.debug
        _log_fn(
            f"[Gathering URLs] session_id={result['session_id']}  "
            f"info={'found' if result['info_url'] else 'missing'}  "
            f"gather={'found' if result['gather_url'] else 'missing'}"
        )
        return result

    def _extract_npc_from_page(self, html: str, url: str = "") -> Optional[int]:
        """
        Try to find a pending NPC encounter ID from the /travel page HTML or redirect URL.
        Returns the NPC ID as int, or None if no encounter is found.

        SimpleMMO shows the NPC encounter panel on the /travel page AFTER a step triggers it.
        The NPC ID can appear in many forms depending on how SMMO renders it.
        """
        import re as _re

        # Check the redirect URL first (highest confidence)
        for pat in [
            r'/npcs/attack/([A-Za-z0-9]+)',
            r'/npcs/battle/([A-Za-z0-9]+)',
            r'/npcs/view/([A-Za-z0-9]+)',
            r'/step-?npc/([A-Za-z0-9]+)',
        ]:
            m = _re.search(pat, url)
            if m:
                try:
                    val = int(m.group(1))
                    self.logger.info(f"[NPC detect] Found NPC ID={val} in redirect URL")
                    return val
                except ValueError:
                    pass

        # Search HTML for NPC ID using every known pattern
        patterns = [
            # Direct URL in HTML
            r'/npcs/attack/([0-9]+)',
            r'/npcs/battle/([0-9]+)',
            r'/npcs/view/([0-9]+)',
            r'/step-?npc/([0-9]+)',
            # Alpine.js / JavaScript data
            r'\bnpc_id["\s]*[=:]\s*["\']?([0-9]+)',
            r'\bnpcId["\s]*[=:]\s*["\']?([0-9]+)',
            # Quoted JSON field in Alpine x-data or game_data
            r'"npc_id"\s*:\s*([0-9]+)',
            r'"npcId"\s*:\s*([0-9]+)',
            r'"step_npc"\s*:\s*([0-9]+)',
            r'"encounter_npc"\s*:\s*([0-9]+)',
            r'"npc\.id"\s*:\s*([0-9]+)',
            # HTML data attributes
            r'data-npc-id=["\']([0-9]+)["\']',
            r'data-enemy-id=["\']([0-9]+)["\']',
            r'data-npc=["\']([0-9]+)["\']',
        ]
        for pat in patterns:
            m = _re.search(pat, html, _re.IGNORECASE)
            if m:
                try:
                    val = int(m.group(1))
                    self.logger.info(f"[NPC detect] Found NPC ID={val} via pattern: {pat}")
                    return val
                except ValueError:
                    pass

        # Log a snippet when the page looks like it has an NPC encounter (for future debugging)
        npc_indicators = [
            'npcs/attack', 'npc_id', 'npcId', 'step_npc', 'encounter',
            'battle-npc', 'fight-npc', 'npc-encounter',
        ]
        if any(ind in html for ind in npc_indicators):
            self.logger.debug(
                f"[NPC detect] Page has NPC-related content but ID not extracted "
                f"-- snippet: {html[:500]!r}"
            )
        return None

    def salvage_material(
        self,
        material_session_id: int,
        quantity: int = None,
        material_name: str = None,
        page_html: str = None,
        gather_url: str = None,
    ) -> Dict[str, Any]:
        """
        Gather materials using the signed API URLs extracted from the travel page.

        Steps:
          1. If no page_html given, re-fetch /travel (to get signed URLs).
          2. Extract signed information + gather URLs via _extract_gathering_urls.
          3. POST information endpoint → verify energy, equipment, get quantity.
          4. POST gather endpoint with JSON body {quantity, id}.
          5. Parse EXP/items from response and return.
        """
        if not self.logged_in:
            return {"success": False, "error": "Not logged in"}
        if not material_session_id:
            return {"success": False, "error": "Invalid material session ID"}

        import re as _re

        try:
            # ── Step 1: get page HTML if not supplied ─────────────────────
            if page_html is None:
                self.logger.debug("salvage_material: fetching /travel for signed URLs")
                import gzip as _gzip
                pr = self.session.get(
                    f"{self.base_url}/travel",
                    headers={"Accept-Encoding": "identity"},
                    allow_redirects=True,
                    timeout=10,
                )
                if pr.status_code == 200:
                    _raw = pr.content
                    if _raw[:2] == b'\x1f\x8b':
                        try:
                            page_html = _gzip.decompress(_raw).decode("utf-8", errors="replace")
                        except Exception:
                            page_html = pr.text
                    else:
                        page_html = pr.text
                else:
                    page_html = ""

            # ── Step 2: extract signed URLs ───────────────────────────────
            g = self._extract_gathering_urls(page_html)
            info_url = g["info_url"]
            # Caller may supply a pre-extracted gather_url (e.g. from travel API response JSON)
            # — only fall back to the page-HTML-extracted URL if none was supplied
            if not gather_url:
                gather_url = g["gather_url"]

            # Override session_id if we extracted a more reliable one from HTML
            if g["session_id"] and not material_session_id:
                material_session_id = g["session_id"]

            api_headers = {
                "X-XSRF-TOKEN":  self.csrf_token,
                "Content-Type":  "application/json",
                "Accept":        "application/json",
                "Origin":        self.base_url,
                "Referer":       f"{self.base_url}/travel",
                "Authorization": f"Bearer {self.api_token}" if self.api_token else "",
            }

            # ── Step 3: information endpoint ──────────────────────────────
            if info_url:
                try:
                    ir = self.session.post(
                        info_url,
                        headers=api_headers,
                        json={"material_session_id": material_session_id},
                        timeout=10,
                    )
                    if ir.status_code == 200:
                        info_data = ir.json()
                        session_data = info_data.get("material_session") or {}
                        mat          = session_data.get("material") or {}

                        # Fill in name / quantity from info response if not already known
                        if material_name is None:
                            material_name = mat.get("name") or session_data.get("item", {}).get("formatted_name")
                            if material_name:
                                # strip HTML tags if name came from formatted_name
                                material_name = _re.sub(r'<[^>]+>', '', material_name)

                        if quantity is None:
                            quantity = session_data.get("amount", 1)

                        action_name = session_data.get("action_name", "Gather")

                        # Check energy availability
                        ep = info_data.get("energy_points") or {}
                        if ep.get("current", 1) < 1:
                            self.logger.warning("Not enough energy for gathering")
                            return {"success": False, "error": "No energy for gathering", "insufficient_energy": True}

                        # Check equipment
                        if session_data.get("correct_equipment") is False:
                            self.logger.warning("Missing required equipment for gathering")
                            return {"success": False, "error": f"Missing required tool for {mat.get('item_type', 'gathering')}", "insufficient_energy": False}

                        # Check level requirement
                        if session_data.get("is_too_low_level") is True:
                            self.logger.warning("Player level too low for this material")
                            return {"success": False, "error": "Level too low for this material"}

                        self.logger.info(
                            f"{action_name}: {material_name or 'material'} "
                            f"x{quantity}  energy={ep.get('current')}/{ep.get('max')}"
                        )
                    else:
                        self.logger.warning(f"Info endpoint HTTP {ir.status_code} — proceeding anyway")
                        if quantity is None:
                            quantity = 1
                except Exception as ie:
                    self.logger.warning(f"Info endpoint error: {ie} — proceeding anyway")
                    if quantity is None:
                        quantity = 1
            else:
                self.logger.warning("No signed info URL found — skipping pre-check")
                if quantity is None:
                    quantity = 1

            # ── Step 4: gather endpoint ───────────────────────────────────
            gr = None  # may be set by fallback loop below
            if not gather_url:
                # No signed URL from page HTML or caller — try known unsigned fallback endpoints.
                # SMMO event materials (e.g. Lunar New Year fireworks) may accept direct POSTs.
                _api_base = "https://api.simple-mmo.com"
                _web_base = self.base_url  # https://web.simple-mmo.com
                _fallback_urls = [
                    f"{_web_base}/api/gathering/material/gather",
                    f"{_api_base}/api/gathering/material/gather",
                    f"{_web_base}/api/gathering/gather",
                    f"{_api_base}/api/gathering/gather",
                ]
                self.logger.warning(
                    f"No signed gather URL — trying {len(_fallback_urls)} direct fallback endpoints "
                    f"for session={material_session_id}"
                )
                for _fb_url in _fallback_urls:
                    try:
                        _fb_r = self.session.post(
                            _fb_url,
                            headers=api_headers,
                            json={"material_session_id": material_session_id, "quantity": quantity or 1, "id": material_session_id},
                            timeout=10,
                        )
                        self.logger.info(
                            f"Fallback gather {_fb_url!r} -> HTTP {_fb_r.status_code} "
                            f"body={_fb_r.text[:200]!r}"
                        )
                        if _fb_r.status_code == 200:
                            _fb_data = _fb_r.json()
                            if _fb_data.get("type") == "success" or _fb_data.get("status") == "success":
                                gather_url = _fb_url   # record which one worked
                                # reuse step-5 parsing below via a synthetic `gr`
                                class _FakeResp:
                                    status_code = 200
                                    def json(self_inner):
                                        return _fb_data
                                gr = _FakeResp()
                                break
                    except Exception as _fb_e:
                        self.logger.debug(f"Fallback {_fb_url!r} error: {_fb_e}")
                        continue
                else:
                    self.logger.error(
                        f"No signed gather URL and all fallbacks failed "
                        f"(session={material_session_id}).  "
                        f"Will log full response on next run when [RAW TRAVEL FULL] fires."
                    )
                    return {"success": False, "error": "Could not find gather URL (signed or fallback)"}

            if not gather_url:
                return {"success": False, "error": "Could not find signed gather URL in page"}

            label = f"'{material_name}'" if material_name else f"session={material_session_id}"
            self.logger.info(f"Gathering {label} x{quantity}")

            if gr is None:  # not set by fallback; do the real POST
                gr = self.session.post(
                    gather_url,
                    headers=api_headers,
                    json={"material_session_id": material_session_id, "quantity": quantity, "id": material_session_id},
                    timeout=15,
                )

            if gr.status_code != 200:
                self.logger.error(f"Gather HTTP {gr.status_code}: {gr.text[:300]}")
                return {"success": False, "error": f"HTTP {gr.status_code}"}

            data = gr.json()

            # ── Step 5: parse response ────────────────────────────────────
            if data.get("type") == "success" or data.get("status") == "success":
                # Primary field
                exp = data.get("player_experience_gained", 0) or 0
                # Fallback: parse from result HTML (e.g. "4,292 EXP")
                if not exp:
                    exp_m = _re.search(r'([\d,]+)\s*EXP', data.get("result", ""))
                    if exp_m:
                        exp = int(exp_m.group(1).replace(",", ""))

                skill_exp = data.get("skill_experience_gained", 0) or 0
                gold      = data.get("gold", 0) or 0
                is_end    = data.get("is_end", True)

                self.logger.info(
                    f"Gathered {quantity}x {material_name or 'material'}: "
                    f"+{exp} EXP  +{skill_exp} skill EXP  is_end={is_end}"
                )
                return {
                    "success":   True,
                    "exp":       exp,
                    "skill_exp": skill_exp,
                    "gold":      gold,
                    "items":     [{"name": material_name or "Material", "quantity": quantity}],
                    "message":   f"Gathered {quantity}x {material_name or 'material'}",
                    "is_end":    is_end,
                }
            else:
                raw_err = data.get("message") or data.get("result") or str(data)
                # Strip HTML tags from error messages
                err = _re.sub(r'<[^>]+>', '', raw_err).strip()
                insuf = any(w in err.lower() for w in ["energy", "stamina", "not enough", "insufficient"])
                self.logger.warning(f"Gather failed: {err}")
                return {"success": False, "error": err, "insufficient_energy": insuf}

        except Exception as e:
            self.logger.error(f"Error gathering material: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def _countdown(self, seconds: float, message: str = "Next travel in"):
        """Display a real-time countdown timer"""
        total_seconds = int(seconds)
        for remaining in range(total_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            timer = f"{mins:02d}:{secs:02d}" if mins > 0 else f"{secs}s"
            print(f"\r{message}: {timer}  ", end='', flush=True)
            time.sleep(1)
        
        # Handle remaining fractional seconds
        fractional = seconds - total_seconds
        if fractional > 0:
            time.sleep(fractional)
        
        print("\r" + " " * 50 + "\r", end='', flush=True)  # Clear the line
    
    def _extract_required_item(self, page_source: str) -> str:
        """Extract the required item name from CAPTCHA page"""
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Look for the "Select the:" text
            text = soup.get_text()
            
            # Pattern: "Select the: ItemName"
            import re
            match = re.search(r'Select the:?\s*([A-Za-z\s]+)', text, re.IGNORECASE)
            if match:
                item_name = match.group(1).strip()
                return item_name
            
            # Alternative pattern
            match = re.search(r'Click (?:on )?the:?\s*([A-Za-z\s]+)', text, re.IGNORECASE)
            if match:
                item_name = match.group(1).strip()
                return item_name
                
        except Exception as e:
            self.logger.debug(f"Failed to extract required item: {e}")
        
        return ""
    
    def _determine_captcha_model(self) -> str:
        """
        Determine which CLIP model to use based on strategy and failure counts.
        Returns 'base' or 'finetuned'
        """
        import os
        
        finetuned_path = "models/clip-captcha-finetuned"
        finetuned_exists = os.path.exists(finetuned_path)
        
        strategy = self.captcha_model_strategy
        threshold = self.captcha_failure_threshold
        
        # If fine-tuned model doesn't exist, always use base
        if not finetuned_exists:
            if strategy == "finetuned_only":
                self.logger.warning("finetuned_only strategy selected but model not found - using base")
            return "base"
        
        # Strategy: base_only - always use base model
        if strategy == "base_only":
            return "base"
        
        # Strategy: finetuned_only - always use fine-tuned model
        if strategy == "finetuned_only":
            return "finetuned"
        
        # Strategy: smart_fallback - switch based on failure counts
        if strategy == "smart_fallback":
            # Initialize current model on first use
            if self.current_captcha_model is None:
                # Start with fine-tuned if available, else base
                self.current_captcha_model = "finetuned"
                self.logger.info(f"🤖 Smart Fallback: Starting with {self.current_captcha_model} model")
            
            # Check if we should switch models
            if self.current_captcha_model == "base":
                if self.base_model_failures >= threshold:
                    self.logger.warning(f"⚠️ Base model failed {self.base_model_failures}x - switching to fine-tuned model")
                    self.current_captcha_model = "finetuned"
                    self.base_model_failures = 0  # Reset counter
            elif self.current_captcha_model == "finetuned":
                if self.finetuned_model_failures >= threshold:
                    self.logger.warning(f"⚠️ Fine-tuned model failed {self.finetuned_model_failures}x - switching to base model")
                    self.current_captcha_model = "base"
                    self.finetuned_model_failures = 0  # Reset counter
            
            return self.current_captcha_model
        
        # Default fallback: use config's use_finetuned_captcha setting
        return "finetuned" if self.config.get("use_finetuned_captcha", False) else "base"
    
    def _record_captcha_result(self, success: bool, model_used: str):
        """
        Track captcha solve result for smart fallback
        Args:
            success: Whether the captcha was solved successfully
            model_used: 'base' or 'finetuned'
        """
        if success:
            # Reset failure counters on success
            if model_used == "base":
                self.base_model_failures = 0
                self.logger.info(f"✅ Base model success - reset failure counter")
            elif model_used == "finetuned":
                self.finetuned_model_failures = 0
                self.logger.info(f"✅ Fine-tuned model success - reset failure counter")
        else:
            # Increment failure counter
            if model_used == "base":
                self.base_model_failures += 1
                self.logger.warning(f"❌ Base model failed ({self.base_model_failures}/{self.captcha_failure_threshold})")
            elif model_used == "finetuned":
                self.finetuned_model_failures += 1
                self.logger.warning(f"❌ Fine-tuned model failed ({self.finetuned_model_failures}/{self.captcha_failure_threshold})")
    
    def _solve_captcha_on_page(self, driver, page_source: str) -> bool:
        """Solve CAPTCHA on an already loaded page (for retries)"""
        try:
            from PIL import Image
            import os
            import torch
            from transformers import CLIPProcessor, CLIPModel
            from io import BytesIO
            
            # Extract required item from current page
            required_item = self._extract_required_item(page_source)
            
            if not required_item:
                self.logger.error("Could not extract required item from page")
                return False
            
            print(f"✓ New CAPTCHA requires clicking: {required_item}")
            self.logger.info(f"New CAPTCHA requires clicking: {required_item}")
            
            # Find buttons
            buttons = []
            try:
                buttons = driver.find_elements(By.XPATH, "//button[contains(@onclick, 'chooseItem')]")
            except:
                try:
                    buttons = driver.find_elements(By.XPATH, "//button[.//img[contains(@src, 'uid=')]]")
                except:
                    pass
            
            if not buttons or len(buttons) < 4:
                self.logger.error(f"Expected 4 buttons, found {len(buttons)}")
                return False
            
            print(f"✓ Found {len(buttons)} CAPTCHA options for new challenge")
            
            # Use smart model selection
            model_choice = self._determine_captcha_model()
            finetuned_path = "models/clip-captcha-finetuned"
            
            if model_choice == "finetuned":
                print(f"🎯 Using fine-tuned CAPTCHA model (failures: {self.finetuned_model_failures}/{self.captcha_failure_threshold})")
                self.logger.info(f"Using fine-tuned model (failures: {self.finetuned_model_failures})")
                model = CLIPModel.from_pretrained(finetuned_path)
                processor = CLIPProcessor.from_pretrained(finetuned_path)
                model_used = "finetuned"
            else:
                print(f"🔵 Using base CLIP model (failures: {self.base_model_failures}/{self.captcha_failure_threshold})")
                self.logger.info(f"Using base model (failures: {self.base_model_failures})")
                model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                model_used = "base"
            
            # Wait for images to load
            time.sleep(2)
            
            # Collect button images with improved error handling
            button_images = []
            for idx, button in enumerate(buttons):
                try:
                    # Try to find img element
                    try:
                        img_element = button.find_element(By.TAG_NAME, 'img')
                    except:
                        img_element = button.find_element(By.CSS_SELECTOR, 'img')
                    
                    # Wait for visibility
                    WebDriverWait(driver, 2).until(EC.visibility_of(img_element))
                    
                    screenshot = img_element.screenshot_as_png
                    if not screenshot:
                        screenshot = button.screenshot_as_png
                    
                    image = Image.open(BytesIO(screenshot)).convert('RGB')
                    button_images.append({'idx': idx, 'button': button, 'image': image})
                except Exception as e:
                    self.logger.warning(f"Error loading button {idx+1}: {e}")
                    # Fallback: screenshot whole button
                    try:
                        screenshot = button.screenshot_as_png
                        image = Image.open(BytesIO(screenshot)).convert('RGB')
                        button_images.append({'idx': idx, 'button': button, 'image': image})
                    except:
                        continue
            
            if len(button_images) < 4:
                self.logger.error(f"Could only load {len(button_images)} button images")
                return False
            
            # AI analysis (same as main CAPTCHA solver)
            text_variations = [
                required_item,
                required_item.lower(),
                required_item.title(),
                required_item.replace(' ', ''),
                f"a {required_item}",
                f"an {required_item}",
                f"the {required_item}",
                f"{required_item} item",
                f"{required_item} object",
                f"picture of {required_item}",
                f"image of {required_item}"
            ]
            
            print(f"  Using {len(text_variations)} text variations for matching")
            self.logger.info(f"Using {len(text_variations)} text variations")
            
            # Process images and text
            inputs = processor(
                text=text_variations,
                images=[img_data['image'] for img_data in button_images],
                return_tensors="pt",
                padding=True
            )
            
            # Get model predictions using the correct ranking direction:
            # softmax across images (dim=0) so each image competes against the others
            # per text prompt, then average win-probability across text variations.
            with torch.no_grad():
                outputs = model(**inputs)
                logits_per_image = outputs.logits_per_image  # [num_images, num_texts]
                probs_per_text   = logits_per_image.softmax(dim=0)  # images compete per text
                avg_probs        = probs_per_text.mean(dim=1)       # [num_images]
            
            # Find best match
            scores = []
            for img_idx in range(len(button_images)):
                score = int(float(avg_probs[img_idx]) * 100)
                scores.append((img_idx, score))
                print(f"  Button {img_idx + 1}: AI confidence = {score}%")
                self.logger.info(f"  Button {img_idx + 1}: AI confidence = {score}%")
            
            scores.sort(key=lambda x: x[1], reverse=True)
            best_idx = scores[0][0] + 1
            best_score = int(scores[0][1])
            second_best_score = int(scores[1][1]) if len(scores) > 1 else 0
            margin = best_score - second_best_score

            # Log confidence warnings
            if best_score < 60:
                print(f"⚠ WARNING: Low AI confidence ({best_score}%) - might be wrong!")
                self.logger.warning(f"Low confidence: {best_score}%")

            if margin < 8:
                self.logger.warning(f"Small margin: {margin}%")

            print(f"\nBest match for new challenge: Button {best_idx} with {best_score}% confidence")
            
            # Click the best match
            best_match = button_images[best_idx - 1]['button']
            print(f"-> Clicking button {best_idx}...")
            best_match.click()
            time.sleep(4)
            
            # Convert button images to bytes for auto-learning
            button_images_bytes = []
            for img_data in button_images:
                try:
                    from io import BytesIO
                    img_bytes = BytesIO()
                    img_data['image'].save(img_bytes, format='PNG')
                    button_images_bytes.append(img_bytes.getvalue())
                except:
                    button_images_bytes.append(None)
            
            # Check result
            current_url = driver.current_url
            page_source = driver.page_source
            
            if '/travel' in current_url or 'already verified' in page_source.lower():
                print("✓ New CAPTCHA solved successfully!")
                self.logger.info("New CAPTCHA solved!")
                
                # Record successful result for smart fallback tracking
                self._record_captcha_result(success=True, model_used=model_used)
                
                # Record successful attempt for auto-learning
                try:
                    from auto_captcha_learner import AutoCaptchaLearner
                    learner = AutoCaptchaLearner()
                    learner.record_attempt(
                        question=required_item,
                        button_clicked=best_idx,
                        success=True,
                        button_images=button_images_bytes
                    )
                except Exception as e:
                    self.logger.debug(f"Auto-learning save failed: {e}")
                
                return True
            else:
                print(f"✗ New CAPTCHA also failed")
                
                # Record failed result for smart fallback tracking
                self._record_captcha_result(success=False, model_used=model_used)
                
                # Record failed attempt for auto-learning
                try:
                    from auto_captcha_learner import AutoCaptchaLearner
                    learner = AutoCaptchaLearner()
                    learner.record_attempt(
                        question=required_item,
                        button_clicked=best_idx,
                        success=False,
                        button_images=button_images_bytes
                    )
                except Exception as e:
                    self.logger.debug(f"Auto-learning save failed: {e}")
                
                return False
            
        except Exception as e:
            self.logger.error(f"Error solving CAPTCHA on page: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False
    
    def _solve_captcha(self, html: str = None) -> bool:
        """Attempt to solve the 'I am not a bot' CAPTCHA challenge using Selenium + Tesseract"""
        driver = None
        try:
            self.logger.info("Initializing browser to load CAPTCHA...")
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'user-agent={self.session.headers["User-Agent"]}')
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set cookies from session
            driver.get(self.base_url)
            time.sleep(1)
            
            # Add session cookies
            for cookie in self.session.cookies:
                try:
                    driver.add_cookie({
                        'name': cookie.name,
                        'value': cookie.value,
                        'domain': cookie.domain,
                        'path': cookie.path
                    })
                except Exception as e:
                    self.logger.debug(f"Could not add cookie {cookie.name}: {e}")
            
            # Navigate to CAPTCHA page
            captcha_url = f"{self.base_url}/i-am-not-a-bot"
            self.logger.info(f"Loading CAPTCHA page in browser...")
            driver.get(captcha_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Wait for the item name to appear
            try:
                item_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'font-semibold') and contains(@class, 'text-')]"))
                )
                required_item = item_element.text.strip()
                print(f"✓ CAPTCHA requires clicking: {required_item}")
                self.logger.info(f"CAPTCHA requires clicking: {required_item}")
            except:
                # Try alternative selectors
                try:
                    page_text = driver.find_element(By.TAG_NAME, 'body').text
                    if 'Please press on the following item' not in page_text:
                        self.logger.warning("CAPTCHA page didn't load properly (no challenge found)")
                        return False
                    
                    # Extract required item from page text
                    lines = [l.strip() for l in page_text.split('\n') if l.strip()]
                    for i, line in enumerate(lines):
                        if 'Please press on the following item' in line and i + 1 < len(lines):
                            required_item = lines[i + 1]
                            print(f"✓ CAPTCHA requires clicking: {required_item}")
                            self.logger.info(f"CAPTCHA requires clicking: {required_item}")
                            break
                    else:
                        self.logger.error("Could not find required item name")
                        return False
                except Exception as e:
                    self.logger.error(f"Could not extract CAPTCHA challenge: {e}")
                    return False
            
            # Find all image buttons - try multiple selectors
            buttons = None
            try:
                # Try Alpine.js x-on:click attribute
                buttons = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[x-on\\:click*='chooseItem']"))
                )
            except:
                try:
                    # Try regular onclick
                    buttons = driver.find_elements(By.XPATH, "//button[contains(@onclick, 'chooseItem')]")
                except:
                    try:
                        # Try finding buttons with images
                        buttons = driver.find_elements(By.XPATH, "//button[.//img[contains(@src, 'uid=')]]")
                    except:
                        pass
            
            if not buttons or len(buttons) == 0:
                self.logger.error("Could not find CAPTCHA image buttons")
                # Save page source for debugging
                with open('captcha_selenium_debug.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                self.logger.info("Saved page to captcha_selenium_debug.html")
                return False
            
            print(f"✓ Found {len(buttons)} CAPTCHA options")
            self.logger.info(f"Found {len(buttons)} CAPTCHA options")
            
            if len(buttons) < 4:
                self.logger.error(f"Expected 4 buttons, found {len(buttons)}")
                return False
            
            # Use CLIP AI model to identify images (works with icons/objects, not just text)
            # Import required modules (local scope to avoid conflicts)
            from PIL import Image
            from io import BytesIO
            import os
            import torch
            from transformers import CLIPProcessor, CLIPModel
            
            try:
                print("Loading AI vision model (CLIP)...")
                self.logger.info("Loading CLIP model for image recognition...")
                
                # Use smart model selection
                model_choice = self._determine_captcha_model()
                finetuned_path = "models/clip-captcha-finetuned"
                
                if model_choice == "finetuned":
                    print(f"🎯 Using fine-tuned CAPTCHA model (failures: {self.finetuned_model_failures}/{self.captcha_failure_threshold})")
                    self.logger.info(f"Using fine-tuned model (failures: {self.finetuned_model_failures})")
                    model = CLIPModel.from_pretrained(finetuned_path)
                    processor = CLIPProcessor.from_pretrained(finetuned_path)
                    model_used = "finetuned"
                else:
                    # Load base CLIP model - this can recognize objects in images
                    print(f"🔵 Using base CLIP model (failures: {self.base_model_failures}/{self.captcha_failure_threshold})")
                    self.logger.info(f"Using base model (failures: {self.base_model_failures})")
                    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                    model_used = "base"
                
                print(f"Analyzing images to find: {required_item}")
                self.logger.info(f"Using AI to identify: {required_item}")
                
                # Create debug folder
                os.makedirs('captcha_ai_debug', exist_ok=True)
                
                # Wait for images to load (important!)
                time.sleep(2)  # Give images time to load
                
                # Collect all button images
                button_images = []
                for idx, button in enumerate(buttons):
                    try:
                        # Strategy 1: Find img tag inside button
                        try:
                            img_element = button.find_element(By.TAG_NAME, 'img')
                        except:
                            # Strategy 2: Find img with CSS selector (more flexible)
                            img_element = button.find_element(By.CSS_SELECTOR, 'img')
                        
                        # Wait a moment for image to be visible
                        WebDriverWait(driver, 2).until(
                            EC.visibility_of(img_element)
                        )
                        
                        # Take screenshot of the image
                        screenshot = img_element.screenshot_as_png
                        
                        if not screenshot:
                            self.logger.warning(f"Button {idx+1}: Screenshot returned empty")
                            # Try taking screenshot of whole button instead
                            screenshot = button.screenshot_as_png
                        
                        image = Image.open(BytesIO(screenshot)).convert('RGB')
                        
                        # Save for debugging
                        image.save(f'captcha_ai_debug/button_{idx+1}.png')
                        self.logger.debug(f"Button {idx+1}: Successfully loaded image ({image.size})")
                        
                        button_images.append({'idx': idx, 'button': button, 'image': image})
                    except Exception as e:
                        self.logger.warning(f"Error loading button {idx+1}: {e}")
                        # Try one more time with whole button screenshot
                        try:
                            screenshot = button.screenshot_as_png
                            image = Image.open(BytesIO(screenshot)).convert('RGB')
                            image.save(f'captcha_ai_debug/button_{idx+1}_fallback.png')
                            button_images.append({'idx': idx, 'button': button, 'image': image})
                            self.logger.debug(f"Button {idx+1}: Used fallback (whole button screenshot)")
                        except Exception as e2:
                            self.logger.error(f"Button {idx+1}: Both strategies failed - {e2}")
                            continue
                
                if not button_images:
                    self.logger.error("Could not load any button images")
                    # Save page source for debugging
                    with open('captcha_image_load_debug.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    self.logger.error("Saved page HTML to captcha_image_load_debug.html for debugging")
                    
                    # Also try to get button HTML structure
                    try:
                        self.logger.error("Button structures:")
                        for idx, button in enumerate(buttons):
                            self.logger.error(f"Button {idx+1}: {button.get_attribute('outerHTML')[:200]}")
                    except:
                        pass
                    
                    return False
                
                self.logger.info(f"Successfully loaded {len(button_images)}/{len(buttons)} button images")
                
                # Prepare text candidates — positive prompts only.
                # CLIP does NOT understand negation, so "NOT a X" is harmful.
                text_variations = [
                    required_item,
                    required_item.lower(),
                    required_item.title(),
                    f"a {required_item.lower()}",
                    f"an {required_item.lower()}",
                    f"the {required_item.lower()}",
                    f"a picture of a {required_item.lower()}",
                    f"an icon showing a {required_item.lower()}",
                    f"a drawing of a {required_item.lower()}",
                    f"a cartoon {required_item.lower()}",
                    f"{required_item.lower()} object",
                ]
                
                print(f"  Using {len(text_variations)} text variations for matching")
                self.logger.info(f"Using {len(text_variations)} text variations")
                
                # BEST PRACTICE: Process all images at once for better comparison
                # CLIP is designed to compare multiple images simultaneously
                all_images = [img_data['image'] for img_data in button_images]
                
                inputs = processor(
                    text=text_variations,
                    images=all_images,  # All 4 images at once
                    return_tensors="pt",
                    padding=True
                )
                
                with torch.no_grad():
                    outputs = model(**inputs)
                    logits_per_image = outputs.logits_per_image  # Shape: [num_images, num_texts]
                    # softmax across images (dim=0): for each text prompt, images compete with each other.
                    # This is the correct direction — mirrors how the auto-labeler works.
                    probs_per_text = logits_per_image.softmax(dim=0)  # [num_images, num_texts]
                    # Average win-probability across all text variations for each image.
                    avg_probs = probs_per_text.mean(dim=1)  # [num_images]
                
                # Build per-button scores from averaged win-probabilities
                button_scores = []
                best_match = None
                best_score = 0
                best_idx = -1
                
                for i, img_data in enumerate(button_images):
                    idx = img_data['idx']
                    score = int(float(avg_probs[i]) * 100)
                    
                    button_scores.append({'idx': idx + 1, 'score': score, 'button': img_data['button']})
                    
                    print(f"  Button {idx+1}: AI confidence = {score}%")
                    self.logger.info(f"  Button {idx+1}: AI confidence = {score}%")
                    
                    if score > best_score:
                        best_score = score
                        best_match = img_data['button']
                        best_idx = idx + 1
                
                # Calculate confidence margin (difference between best and second best)
                sorted_scores = sorted(button_scores, key=lambda x: x['score'], reverse=True)
                if len(sorted_scores) >= 2:
                    margin = sorted_scores[0]['score'] - sorted_scores[1]['score']
                    print(f"\nScore margin (best vs 2nd): {margin}%")
                    self.logger.info(f"Score margin: {margin}%")
                else:
                    margin = 100
                
                print(f"\nBest match: Button {best_idx} with {best_score}% confidence")
                self.logger.info(f"Best match: Button {best_idx} with {best_score}% confidence")

                # Log confidence warnings
                # With dim=0 softmax, random baseline = 100/4 = 25%.
                # A confident correct pick should be >=40%.
                if best_score < 40:
                    print(f"⚠ WARNING: Low AI confidence ({best_score}%) - might be wrong!")
                    self.logger.warning(f"Low confidence: {best_score}%")
                
                if margin < 8:
                    self.logger.warning(f"Small margin: {margin}%")

                if best_match:
                    print(f"-> Clicking button {best_idx} (best guess)...")
                    self.logger.info(f"Clicking button {best_idx} with {best_score}% confidence and {margin}% margin...")
                    best_match.click()
                    
                    # Convert button images to bytes for auto-learning
                    button_images_bytes = []
                    for img_data in button_images:
                        try:
                            from io import BytesIO
                            img_bytes = BytesIO()
                            img_data['image'].save(img_bytes, format='PNG')
                            button_images_bytes.append(img_bytes.getvalue())
                        except:
                            button_images_bytes.append(None)
                    
                    # Wait for page to process and redirect
                    print("  Waiting for verification...")
                    time.sleep(4)  # Give more time for redirect
                    
                    # Check if successful - multiple indicators
                    try:
                        current_url = driver.current_url
                        page_source = driver.page_source
                        
                        # Success indicators (check in order of reliability)
                        # 1. Redirected to travel page
                        redirected_to_travel = '/travel' in current_url and 'i-am-not-a-bot' not in current_url
                        
                        # 2. Verification message appears
                        success_message = (
                            'You are already verified' in page_source or 
                            'already verified' in page_source.lower() or
                            'Successfully verified' in page_source or
                            'successfully verified' in page_source.lower()
                        )
                        
                        # 3. CAPTCHA form disappeared (no more challenge)
                        captcha_form_gone = 'chooseItem' not in page_source
                        
                        # 4. Check if still on CAPTCHA page with new challenge
                        still_on_captcha = 'i-am-not-a-bot' in current_url and 'chooseItem' in page_source
                        
                        self.logger.info(f"Success check: redirected={redirected_to_travel}, message={success_message}, form_gone={captcha_form_gone}, still_captcha={still_on_captcha}")
                        
                        if redirected_to_travel or success_message:
                            print("✓ CAPTCHA solved successfully!")
                            self.logger.info("CAPTCHA solved successfully with AI!")
                            
                            # Record successful result for smart fallback tracking
                            self._record_captcha_result(success=True, model_used=model_used)
                            
                            # Record successful attempt for auto-learning
                            try:
                                from auto_captcha_learner import AutoCaptchaLearner
                                learner = AutoCaptchaLearner()
                                learner.record_attempt(
                                    question=required_item,
                                    button_clicked=best_idx,
                                    success=True,
                                    button_images=button_images_bytes
                                )
                            except Exception as e:
                                self.logger.debug(f"Auto-learning save failed: {e}")
                            
                            return True
                        elif not still_on_captcha and captcha_form_gone:
                            # Form is gone and not on CAPTCHA page anymore
                            print("✓ CAPTCHA solved successfully!")
                            self.logger.info("CAPTCHA solved - form disappeared")
                            
                            # Record successful result for smart fallback tracking
                            self._record_captcha_result(success=True, model_used=model_used)
                            
                            # Record successful attempt for auto-learning
                            try:
                                from auto_captcha_learner import AutoCaptchaLearner
                                learner = AutoCaptchaLearner()
                                learner.record_attempt(
                                    question=required_item,
                                    button_clicked=best_idx,
                                    success=True,
                                    button_images=button_images_bytes
                                )
                            except Exception as e:
                                self.logger.debug(f"Auto-learning save failed: {e}")
                            
                            return True
                        else:
                            # Double-check by visiting the CAPTCHA page again
                            self.logger.info("Verification unclear - checking CAPTCHA page again...")
                            driver.get(f"{self.base_url}/i-am-not-a-bot")
                            time.sleep(2)
                            
                            final_page = driver.page_source
                            final_url = driver.current_url
                            
                            # If we see "already verified" or got redirected away, it worked!
                            if ('already verified' in final_page.lower() or 
                                'You are already verified' in final_page or
                                '/travel' in final_url):
                                print("✓ CAPTCHA solved successfully! (confirmed on re-check)")
                                self.logger.info("CAPTCHA verified on second check")
                                
                                # Record successful attempt for auto-learning
                                try:
                                    from auto_captcha_learner import AutoCaptchaLearner
                                    learner = AutoCaptchaLearner()
                                    learner.record_attempt(
                                        question=required_item,
                                        button_clicked=best_idx,
                                        success=True,
                                        button_images=button_images_bytes
                                    )
                                except Exception as e:
                                    self.logger.debug(f"Auto-learning save failed: {e}")
                                
                                # Record successful result for smart fallback tracking
                                self._record_captcha_result(success=True, model_used=model_used)
                                
                                return True
                            
                            # Still on CAPTCHA page - check what happened
                            # 1. Check for cooldown/lockout message
                            soup = BeautifulSoup(final_page, 'html.parser')
                            page_text = soup.get_text().lower()
                            
                            has_cooldown = any(phrase in page_text for phrase in [
                                'try again in', 'wait', 'cooldown', 'locked out', 
                                'too many attempts', 'slow down'
                            ])
                            
                            if has_cooldown:
                                self.logger.warning("CAPTCHA cooldown detected")
                                print(f"⏱️  CAPTCHA cooldown/lockout detected")
                                print(f"  AI picked button {best_idx} (confidence: {best_score}%)")
                                
                                # Record failed result for smart fallback tracking
                                self._record_captcha_result(success=False, model_used=model_used)
                                
                                # Record failed attempt for auto-learning
                                try:
                                    from auto_captcha_learner import AutoCaptchaLearner
                                    learner = AutoCaptchaLearner()
                                    learner.record_attempt(
                                        question=required_item,
                                        button_clicked=best_idx,
                                        success=False,
                                        button_images=button_images_bytes
                                    )
                                except Exception as e:
                                    self.logger.debug(f"Auto-learning save failed: {e}")
                                
                                return False
                            
                            # 2. Check if question changed (new challenge)
                            try:
                                new_required_item = self._extract_required_item(final_page)
                                if new_required_item and new_required_item.lower() != required_item.lower():
                                    self.logger.info(f"CAPTCHA question changed: '{required_item}' -> '{new_required_item}'")
                                    print(f"\n🔄 CAPTCHA question changed!")
                                    print(f"  Previous: {required_item}")
                                    print(f"  New: {new_required_item}")
                                    print(f"  Attempting to solve new challenge...\n")
                                    
                                    # Record failed result for smart fallback tracking
                                    self._record_captcha_result(success=False, model_used=model_used)
                                    
                                    # Record failed attempt for auto-learning
                                    try:
                                        from auto_captcha_learner import AutoCaptchaLearner
                                        learner = AutoCaptchaLearner()
                                        learner.record_attempt(
                                            question=required_item,
                                            button_clicked=best_idx,
                                            success=False,
                                            button_images=button_images_bytes
                                        )
                                    except Exception as e:
                                        self.logger.debug(f"Auto-learning save failed: {e}")
                                    
                                    # Recursively retry with new question (max 2 retries)
                                    if not hasattr(self, '_captcha_retry_count'):
                                        self._captcha_retry_count = 0
                                    
                                    if self._captcha_retry_count < 2:
                                        self._captcha_retry_count += 1
                                        self.logger.info(f"Retry attempt {self._captcha_retry_count}/2")
                                        # Continue solving with the page already loaded
                                        retry_result = self._solve_captcha_on_page(driver, final_page)
                                        self._captcha_retry_count = 0  # Reset counter
                                        return retry_result
                                    else:
                                        self.logger.warning("Max CAPTCHA retries reached")
                                        print("  Max retries reached (2), stopping.")
                                        self._captcha_retry_count = 0
                                        return False
                            except:
                                pass
                            
                            # 3. Wrong answer, same question
                            self.logger.warning("CAPTCHA submission failed - wrong answer")
                            print(f"✗ Wrong answer - AI picked button {best_idx}")
                            print(f"  Confidence was {best_score}% with {margin}% margin")
                            
                            # Record failed result for smart fallback tracking
                            self._record_captcha_result(success=False, model_used=model_used)
                            
                            # Record failed attempt for auto-learning
                            try:
                                from auto_captcha_learner import AutoCaptchaLearner
                                learner = AutoCaptchaLearner()
                                learner.record_attempt(
                                    question=required_item,
                                    button_clicked=best_idx,
                                    success=False,
                                    button_images=button_images_bytes
                                )
                            except Exception as e:
                                self.logger.debug(f"Auto-learning save failed: {e}")
                            
                            return False
                    except Exception as check_error:
                        self.logger.error(f"Error checking CAPTCHA result: {check_error}")
                        # If we can't check, assume failure
                        return False
                else:
                    self.logger.error("No button found to click")
                    print("✗ Could not find any buttons to click")
                    return False
                    
            except ImportError as e:
                self.logger.error("Required AI libraries not available")
                self.logger.error("Install: pip install torch transformers pillow")
                print("\n✗ Missing AI libraries for CAPTCHA solving")
                print("  Install with: pip install torch transformers pillow")
                return False
            except Exception as e:
                self.logger.error(f"AI model error: {e}")
                import traceback
                self.logger.debug(traceback.format_exc())
                print(f"\n✗ AI error: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error solving CAPTCHA: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False
            
        finally:
            if driver:
                driver.quit()
    
    def _identify_captcha_image(self, button_data: List[Dict], required_item: str) -> Optional[str]:
        """Download images and identify the correct one"""
        if not self.has_pil:
            self.logger.error("PIL not available for image analysis")
            return None
        
        from PIL import Image
        
        self.logger.info(f"Downloading {len(button_data)} CAPTCHA images...")
        
        # Download all images
        images = []
        for data in button_data:
            try:
                img_url = f"{self.base_url}/i-am-not-a-bot/generate_image?uid={data['uid']}"
                response = self.session.get(img_url)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    images.append({'hash': data['hash'], 'uid': data['uid'], 'image': img})
                    self.logger.info(f"  Downloaded image uid={data['uid']}")
            except Exception as e:
                self.logger.error(f"Error downloading image uid={data['uid']}: {e}")
        
        if not images:
            return None
        
        # Try OCR if available
        try:
            import pytesseract
            
            self.logger.info("Using OCR to identify images...")
            for img_data in images:
                # Try to extract text from image
                text = pytesseract.image_to_string(img_data['image']).strip().lower()
                required_lower = required_item.lower()
                
                self.logger.info(f"  uid={img_data['uid']}: OCR text='{text}'")
                
                if required_lower in text or text in required_lower:
                    self.logger.info(f"  ✓ Match found! uid={img_data['uid']}")
                    return img_data['hash']
        except ImportError:
            self.logger.warning("pytesseract not available - install it for OCR support")
            self.logger.warning("Install: pip install pytesseract + Tesseract-OCR binary")
        except Exception as e:
            self.logger.error(f"OCR error: {e}")
        
        # Fallback: Save images for manual inspection
        self.logger.warning("Could not identify image automatically")
        self.logger.info("Saving images to captcha_images/ for manual inspection...")
        
        import os
        os.makedirs('captcha_images', exist_ok=True)
        for img_data in images:
            path = f"captcha_images/uid_{img_data['uid']}_hash_{img_data['hash'][:10]}.png"
            img_data['image'].save(path)
            self.logger.info(f"  Saved: {path}")
        
        return None
    
    def _submit_captcha_answer(self, item_hash: str) -> bool:
        """Submit the CAPTCHA answer"""
        try:
            # The chooseItem function likely POSTs to a verification endpoint
            # We need to find the actual endpoint by inspecting the JavaScript
            # For now, try common patterns
            
            endpoints = [
                f"{self.base_url}/i-am-not-a-bot/verify",
                f"{self.base_url}/i-am-not-a-bot/check",
                f"{self.base_url}/api/verify-human",
            ]
            
            data = {
                'item': item_hash,
                '_token': self.csrf_token
            }
            
            for endpoint in endpoints:
                self.logger.info(f"Trying CAPTCHA submission to: {endpoint}")
                response = self.session.post(endpoint, data=data)
                
                if response.status_code == 200:
                    self.logger.info("CAPTCHA submission successful!")
                    return True
                elif response.status_code != 404:
                    self.logger.warning(f"CAPTCHA endpoint returned {response.status_code}")
            
            self.logger.error("Could not find correct CAPTCHA submission endpoint")
            self.logger.info("You may need to manually complete the verification")
            return False
            
        except Exception as e:
            self.logger.error(f"Error submitting CAPTCHA: {e}")
            return False
    
    def attack_npc(self, npc_id: int) -> Dict[str, Any]:
        """Attack an NPC during travel using the proven signed-URL approach (same as BA bot).

        Steps:
          1. GET /npcs/attack/{npc_id} and extract the signed API URL from the page HTML.
          2. POST to the signed URL with JSON body until victory, defeat, or safety cap.

        Returns {"success": True/False, "data": {"exp", "gold", "damage", "attacks", "message", "victory"}}
        """
        if not self.logged_in:
            self.logger.error("Not logged in")
            return {"success": False, "error": "Not logged in"}

        import re as _re

        try:
            self.logger.info(f"Attacking NPC ID: {npc_id}...")

            # ── Step 1: GET NPC page and extract signed attack URL ────────────
            # Use ?new_page=true to match the browser href from the travel API text.
            html = self._fetch_html(
                f"{self.base_url}/npcs/attack/{npc_id}?new_page=true",
                headers={"Referer": f"{self.base_url}/travel"},
            )
            if not html:
                self.logger.error(f"Failed to load NPC page (empty response)")
                return {"success": False, "error": "Empty NPC page response"}
            attack_url = None

            # Pattern 1: plain absolute URL on web.simple-mmo.com OR api.simple-mmo.com
            _m = _re.search(
                r'(https://(?:web|api)\.simple-mmo\.com/api/npcs/attack/[A-Za-z0-9]+'
                r'\?expires=\d+&(?:amp;)?signature=[a-f0-9]+)',
                html,
            )
            if _m:
                attack_url = _m.group(1).replace("&amp;", "&")
                self.logger.info(f"Signed URL (plain): {attack_url}")

            if not attack_url:
                # Pattern 2: JSON-escaped — \/ slashes and \u0026 ampersand
                _m = _re.search(
                    r'https:\\/\\/(?:web|api)\.simple-mmo\.com\\/api\\/npcs\\/attack\\/([A-Za-z0-9]+)'
                    r'\?expires=(\d+)(?:\\u0026|&(?:amp;)?)signature=([a-f0-9]+)',
                    html,
                )
                if _m:
                    attack_url = (
                        f"{self.base_url}/api/npcs/attack/{_m.group(1)}"
                        f"?expires={_m.group(2)}&signature={_m.group(3)}"
                    )
                    self.logger.info(f"Signed URL (JSON-escaped): {attack_url}")

            if not attack_url:
                # Pattern 3: assemble from separate token + expires + signature fields
                # Token can be short alphanumeric OR a long numeric instance ID
                _tok = _re.search(r'/api/npcs/attack/([A-Za-z0-9]{4,20})[\'"\s?]', html)
                _exp = _re.search(r'expires["\']?\s*[=:]\s*["\']?(\d{10,})', html)
                _sig = _re.search(r'signature["\']?\s*[=:]\s*["\']?([a-f0-9]{40,})', html)
                if _tok and _exp and _sig:
                    attack_url = (
                        f"{self.base_url}/api/npcs/attack/{_tok.group(1)}"
                        f"?expires={_exp.group(1)}&signature={_sig.group(1)}"
                    )
                    self.logger.info(f"Signed URL (assembled): {attack_url}")

            if not attack_url:
                # Log a chunk of the page so we can see the actual URL format
                self.logger.warning(
                    f"No signed URL found in NPC page (len={len(html)}, "
                    f"final_url={page_resp.url!r}).\n"
                    f"[NPC PAGE SNIPPET] {html[:1500]!r}"
                )
                return {"success": False, "error": "No signed attack URL found in NPC page"}

            self.logger.info(f"Attack URL: {attack_url}")

            # ── Step 2: Attack loop (same headers as Battle Arena bot) ─────────
            attack_headers = {
                "X-XSRF-TOKEN":  self.csrf_token,
                "Content-Type":  "application/json",
                "Accept":        "application/json",
                "Origin":        self.base_url,
                "Referer":       f"{self.base_url}/travel",
                "Authorization": f"Bearer {self.api_token}" if self.api_token else "",
            }

            total_damage = 0
            total_exp    = 0
            total_gold   = 0
            attack_count = 0
            max_attacks  = 100  # safety cap

            while attack_count < max_attacks:
                attack_count += 1

                try:
                    r = self.session.post(
                        attack_url,
                        headers=attack_headers,
                        json={
                            "npc_id":         npc_id,
                            "special_attack": False,
                            "api_token":      self.api_token or "",
                        },
                        timeout=15,
                    )
                except Exception as req_e:
                    self.logger.error(f"Attack request error: {req_e}")
                    time.sleep(1)
                    continue

                if r.status_code != 200:
                    self.logger.error(f"Attack HTTP {r.status_code}: {r.text[:300]}")
                    # Non-retriable errors — abort immediately instead of retrying 100 times
                    if r.status_code in (404, 401, 403, 410):
                        self.logger.error(
                            f"Fatal attack error (HTTP {r.status_code}) — "
                            f"aborting battle with NPC {npc_id}"
                        )
                        return {"success": False, "error": f"HTTP {r.status_code}"}
                    time.sleep(1)
                    continue

                try:
                    d = r.json()
                except Exception:
                    time.sleep(0.5)
                    continue

                t         = (d.get("type") or "").lower()
                player_hp = d.get("player_hp", "?")
                opp_hp    = d.get("opponent_hp", "?")
                dmg       = d.get("damage_given_to_opponent", d.get("damage", 0)) or 0
                if isinstance(dmg, (int, float)):
                    total_damage += dmg

                self.logger.info(
                    f"Attack #{attack_count}: dealt={dmg}  "
                    f"enemy_hp={opp_hp}  your_hp={player_hp}  type={t}"
                )

                # ── Victory ──────────────────────────────────────────────────
                if (t == "success"
                        or "winner" in (d.get("title") or "").lower()
                        or d.get("npc_killed") is True
                        or d.get("battle_over") is True
                        or (isinstance(opp_hp, (int, float)) and opp_hp <= 0)):

                    self.logger.info(f"Battle WON after {attack_count} attacks!")

                    # Parse rewards — try structured rewards list first
                    rewards = d.get("rewards") or []
                    for rw in rewards:
                        if isinstance(rw, dict):
                            total_exp  += rw.get("exp",  rw.get("experience", 0)) or 0
                            total_gold += rw.get("gold", rw.get("coins",      0)) or 0

                    if total_exp == 0:
                        total_exp  = d.get("exp",  d.get("experience", 0)) or 0
                        total_gold = d.get("gold", d.get("coins",      0)) or 0

                    if total_exp == 0:
                        # Last resort: parse "20,893 Total EXP" from result HTML
                        result_html = d.get("result") or ""
                        _em = _re.search(r"([\d,]+)\s*Total\s*EXP", result_html)
                        if _em:
                            total_exp = int(_em.group(1).replace(",", ""))

                    return {
                        "success": True,
                        "data": {
                            "exp":     total_exp,
                            "gold":    total_gold,
                            "damage":  int(total_damage),
                            "attacks": attack_count,
                            "message": d.get("title", ""),
                            "victory": True,
                        },
                    }

                # ── Defeat ───────────────────────────────────────────────────
                if ((isinstance(player_hp, (int, float)) and player_hp <= 0)
                        or d.get("player_hp_percentage", 100) == 0):
                    self.logger.warning(f"Defeated after {attack_count} attacks")
                    return {
                        "success": False,
                        "error":   "defeated",
                        "data": {
                            "exp": 0, "gold": 0,
                            "damage": int(total_damage), "attacks": attack_count,
                            "message": "Defeated", "victory": False,
                        },
                    }

                # ── Error ────────────────────────────────────────────────────
                if t == "error":
                    err = d.get("message", "Unknown battle error")
                    self.logger.error(f"Battle error: {err}")
                    return {"success": False, "error": err}

                time.sleep(0.3)

            # Safety cap reached
            self.logger.warning(f"Battle did not complete after {max_attacks} attacks")
            return {"success": False, "error": f"Battle timeout after {max_attacks} attacks"}

        except Exception as e:
            self.logger.error(f"NPC attack error: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def travel(self) -> Dict[str, Any]:
        """Perform a travel action (Take a Step)"""
        if not self.logged_in:
            self.logger.error("Not logged in")
            return {"success": False, "error": "Not logged in"}
        
        if not self.api_token:
            self.logger.error("No API token available")
            return {"success": False, "error": "No API token - refresh session"}
        
        # First check if we're currently in an NPC battle or material gathering
        npc_battle_data = None
        material_gather_data = None
        page_html = None  # pre-travel page; also used as fallback HTML for gathering
        
        try:
            page_html = self._fetch_html(f"{self.base_url}/travel")
            
            import re
            # ── Pre-travel: detect pending material encounter ─────────────────
            # Use _extract_gathering_urls which handles all known patterns + signed URLs
            _pretrav_g = self._extract_gathering_urls(page_html)
            material_session_id = _pretrav_g.get("session_id")

            if material_session_id:
                self.logger.info(
                    f"Pre-travel: gathering encounter detected "
                    f"(session_id={material_session_id}, "
                    f"info={'found' if _pretrav_g['info_url'] else 'missing'}, "
                    f"gather={'found' if _pretrav_g['gather_url'] else 'missing'})"
                )
                # Auto-gather if enabled — pass the already-fetched page HTML
                if self.config.get("auto_gather_materials", True):
                    self.logger.info("Auto-gathering material before travel step...")
                    gather_result = self.salvage_material(
                        material_session_id, page_html=page_html
                    )
                    if gather_result.get("success"):
                        material_gather_data = gather_result
                        self.logger.info("Material gathered successfully, continuing with travel...")
                    else:
                        error_msg = gather_result.get("error", "Unknown error")
                        self.logger.warning(f"Material gathering failed: {error_msg}")
                        material_gather_data = {
                            "success": False, "error": error_msg,
                            "insufficient_energy": gather_result.get("insufficient_energy", False),
                        }
            
            # ── Pre-travel: detect pending NPC battle ──────────────────────────
            # Use the comprehensive extractor (URL redirect + all HTML patterns)
            npc_id_pretrav = self._extract_npc_from_page(page_html, f"{self.base_url}/travel")

            if npc_id_pretrav:
                npc_id = npc_id_pretrav
                self.logger.info(f"Pre-travel: detected pending NPC battle (ID: {npc_id})")

                # Auto-battle if enabled
                if self.config.get("auto_battle_npcs", True):
                    self.logger.info("Auto-battling NPC before continuing travel...")
                    battle_result = self.attack_npc(npc_id)

                    if not battle_result.get("success"):
                        return {
                            "success": False,
                            "error": f"NPC battle failed: {battle_result.get('error')}",
                            "npc_encounter": True,
                            "npc_battle": battle_result
                        }

                    # Store battle data to include in travel result
                    npc_battle_data = battle_result.get("data", {"victory": True})
                    self.logger.info("NPC defeated, continuing with travel...")
                else:
                    return {
                        "success": False,
                        "error": "NPC encounter blocking travel (auto_battle_npcs is disabled)",
                        "npc_encounter": True,
                        "npc_id": npc_id
                    }
        except Exception as e:
            self.logger.warning(f"Failed to check for NPC encounter: {e}")
            # Continue with travel attempt anyway
        
        # The real API endpoint is on api.simple-mmo.com, not web.simple-mmo.com
        # From Network tab: POST https://api.simple-mmo.com/api/action/travel/4
        api_url = "https://api.simple-mmo.com/api/action/travel/4"
        
        try:
            self.logger.info("Taking a travel step via API...")
            
            headers = {
                'X-XSRF-TOKEN': self.csrf_token,
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'Accept': '*/*',
                'Origin': 'https://web.simple-mmo.com',
                'Referer': 'https://web.simple-mmo.com/travel',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
            }
            
            # Form data based on browser's actual request
            form_data = {
                '_token': self.csrf_token,
                'api_token': self.api_token,
                'd_1': '376',  # These might be dynamic - may need to extract from page
                'd_2': '385',
                's': 'false',
                'travel_id': '0'
            }
            
            response = self.session.post(api_url, headers=headers, data=form_data)
            
            if response.status_code == 200:
                try:
                    result_data = response.json()
                    self.logger.info("Travel step completed successfully")
                    
                    # Parse the results
                    parsed = self._parse_travel_results(result_data)
                    
                    import re as _re

                    # ── If material detected but no session ID → re-fetch travel page ──
                    if parsed.get("material_encounter") and not parsed.get("material_session_id"):
                        self.logger.info("Material encounter detected — re-fetching /travel page for signed URLs...")
                        try:
                            ph = self._fetch_html(f"{self.base_url}/travel")
                            self.logger.debug(f"[TRAVEL PAGE SNIPPET] {ph[:600]}")

                            g2 = self._extract_gathering_urls(ph)
                            if g2["session_id"]:
                                parsed["material_session_id"] = g2["session_id"]
                                self.logger.info(f"Found material session_id={g2['session_id']} from refetched page")
                            else:
                                self.logger.warning(
                                    "Could not find material session ID on /travel page — skipping gather"
                                )
                                parsed["material_encounter"] = False
                                ph = None
                        except Exception as e:
                            self.logger.error(f"Error re-fetching /travel for material: {e}")
                            parsed["material_encounter"] = False
                            ph = None
                    else:
                        # Session ID came from travel API — no re-fetch needed.
                        # Reuse the pre-travel page HTML so salvage_material has the
                        # gathering modal's signed URLs without an extra network call.
                        ph = page_html

                    # ── Gather material if we now have a session ID ──────────────
                    if parsed.get("material_encounter") and parsed.get("material_session_id") and not material_gather_data:
                        if self.config.get("auto_gather_materials", True):
                            msid = parsed["material_session_id"]
                            _pre_gather_url = parsed.get("material_gather_url")
                            self.logger.info(
                                f"Gathering material (session={msid}"
                                f"{', pre-url='+repr(_pre_gather_url) if _pre_gather_url else ''})"
                            )
                            # Pass refetched/pre-travel page HTML so signed URLs don't need another fetch
                            _html_for_gather = ph  # may be pre-travel page or a fresh re-fetch
                            if _html_for_gather and "gathering" in _html_for_gather:
                                import re as _redebug
                                _gat_m = _redebug.search(r'.{0,300}gathering.{0,300}', _html_for_gather, _redebug.IGNORECASE)
                                self.logger.debug(f"[GATHER HTML SNIPPET] {_gat_m.group(0)!r}" if _gat_m else "[GATHER HTML SNIPPET] no match")
                                _exp_m = _redebug.search(r'.{0,200}expires.{0,200}', _html_for_gather, _redebug.IGNORECASE)
                                self.logger.debug(f"[EXPIRES SNIPPET] {_exp_m.group(0)!r}" if _exp_m else "[EXPIRES SNIPPET] not found in page")
                            gr = self.salvage_material(msid, page_html=_html_for_gather, gather_url=_pre_gather_url)
                            if gr.get("success"):
                                material_gather_data = gr
                                self.logger.info("Material gathered after travel step.")
                            else:
                                self.logger.warning(f"Material gather failed: {gr.get('error')}")

                    # ── Attack NPC detected in travel API response ────────────────
                    if parsed.get("npc_encounter") and parsed.get("npc_id") and not npc_battle_data:
                        if self.config.get("auto_battle_npcs", True):
                            _enc_npc_id   = parsed["npc_id"]
                            _enc_npc_name = parsed.get("npc_name") or "Unknown NPC"
                            self.logger.info(
                                f"NPC encounter in travel response: "
                                f"attacking {_enc_npc_name!r} (ID={_enc_npc_id})"
                            )
                            _br = self.attack_npc(_enc_npc_id)
                            if _br.get("success"):
                                npc_battle_data = _br.get("data", {"victory": True})
                                self.logger.info(f"NPC {_enc_npc_name!r} defeated!")
                            else:
                                self.logger.warning(
                                    f"NPC battle failed: {_br.get('error')}"
                                )
                        else:
                            self.logger.info(
                                f"NPC encounter detected (ID={parsed['npc_id']}) "
                                f"but auto_battle_npcs is disabled — skipping"
                            )

                    # Include NPC/material battle data collected so far
                    result = {"success": True, "data": result_data, "parsed": parsed}
                    if npc_battle_data:
                        result["npc_battle"] = npc_battle_data
                    if material_gather_data:
                        result["material_gather"] = material_gather_data

                    # ── Post-travel page check (UNCONDITIONAL) ───────────────────
                    # SMMO shows NPC encounters and material gathers on the /travel page
                    # AFTER a step — not in the travel API response payload.
                    # We re-fetch /travel after every step to catch them.
                    if not npc_battle_data or not material_gather_data:
                        try:
                            self.logger.info("Post-travel: fetching /travel to check for NPC/material...")
                            pt_html = self._fetch_html(f"{self.base_url}/travel")
                            pt_final_url = f"{self.base_url}/travel"
                            # Log full snippet when the page looks like it has an encounter
                            # (encounter keywords present), otherwise brief
                            _has_encounter_hint = (
                                "npcs/attack" in pt_html[:4000].lower()
                                or "npc_id" in pt_html[:4000].lower()
                                or "battle_npc" in pt_html[:4000].lower()
                                or "material_session" in pt_html[:4000].lower()
                                or "gathering_session" in pt_html[:4000].lower()
                                or "gathering/material" in pt_html[:4000].lower()
                            )
                            if _has_encounter_hint:
                                self.logger.info(
                                    f"[POST-TRAVEL ENCOUNTER HINT] "
                                    f"len={len(pt_html)} snippet={pt_html[:2000]!r}"
                                )
                            else:
                                self.logger.info(
                                    f"Post-travel page: len={len(pt_html)} (no encounter keywords)"
                                )

                            # Material check (if not already gathered this step)
                            if not material_gather_data and self.config.get("auto_gather_materials", True):
                                pt_g = self._extract_gathering_urls(pt_html)
                                if pt_g.get("session_id"):
                                    self.logger.info(
                                        f"Post-travel: material encounter found "
                                        f"(session_id={pt_g['session_id']})"
                                    )
                                    gr = self.salvage_material(pt_g["session_id"], page_html=pt_html)
                                    if gr.get("success"):
                                        material_gather_data = gr
                                        result["material_gather"] = material_gather_data
                                        self.logger.info("Post-travel: material gathered successfully.")
                                    else:
                                        self.logger.warning(
                                            f"Post-travel: material gather failed: {gr.get('error')}"
                                        )

                            # NPC check (if not already battled this step)
                            if not npc_battle_data and self.config.get("auto_battle_npcs", True):
                                pt_npc_id = self._extract_npc_from_page(pt_html, f"{self.base_url}/travel")
                                if pt_npc_id:
                                    self.logger.info(
                                        f"Post-travel: NPC encounter found (ID={pt_npc_id})"
                                    )
                                    battle_result = self.attack_npc(pt_npc_id)
                                    if battle_result.get("success"):
                                        result["npc_battle"] = battle_result.get(
                                            "data", {"victory": True}
                                        )
                                        npc_battle_data = result["npc_battle"]
                                        self.logger.info("Post-travel: NPC defeated.")
                                    else:
                                        self.logger.warning(
                                            f"Post-travel: NPC battle failed: "
                                            f"{battle_result.get('error')}"
                                        )

                        except Exception as e:
                            self.logger.warning(f"Post-travel check failed: {e}")

                    return result
                except Exception as e:
                    # Travel API returned non-JSON (could be NPC page HTML or error page)
                    self.logger.warning(
                        f"Travel API response was not JSON: {e} — "
                        f"raw={response.text[:600]!r}"
                    )
                    result = {"success": True, "data": {}, "parsed": {}}
                    if npc_battle_data:
                        result["npc_battle"] = npc_battle_data
                    if material_gather_data:
                        result["material_gather"] = material_gather_data
                    return result
            elif response.status_code == 429:
                return {"success": False, "error": "Rate limited / Cooldown"}
            elif response.status_code == 403:
                self.logger.error("HTTP 403 - Session may have expired")
                
                # Try to re-login with email/password if available
                email = self.config.get("email")
                password = self.config.get("password")
                if email and password:
                    self.logger.info("Attempting to re-login with email/password...")
                    if self.login(force_email_login=True):
                        self.logger.info("Re-login successful, retrying travel...")
                        # Retry the travel request
                        return self.travel()
                
                return {"success": False, "error": "Session expired - get fresh tokens"}
            else:
                self.logger.error(f"HTTP {response.status_code} - Response: {response.text[:200]}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Travel error: {e}")
            return {"success": False, "error": str(e)}

    
    def auto_travel_loop(self, iterations: int = None):
        """Continuously perform travel actions"""
        if not self.logged_in:
            self.logger.error("Not logged in")
            return
        
        self.logger.info("Starting auto-travel loop")
        count = 0
        
        while True:
            if iterations and count >= iterations:
                self.logger.info(f"Completed {iterations} travel iterations")
                break
            
            # Perform travel
            result = self.travel()
            
            if result.get("success"):
                count += 1
                parsed = result.get("parsed", {})
                
                # Check for CAPTCHA
                if parsed.get("captcha"):
                    print(f"\n{'='*60}")
                    print("⚠️  CAPTCHA CHALLENGE DETECTED")
                    print(f"{'='*60}")
                    
                    if self.config.get("auto_solve_captcha", False):
                        print("\nAttempting to solve CAPTCHA automatically...")
                        print("Using AI vision model (CLIP) to identify images...\n")
                        
                        # Use Selenium + CLIP AI to solve
                        if self._solve_captcha():
                            print("✓ CAPTCHA solved! Continuing...\n")
                            print(f"{'='*60}\n")
                            continue  # Continue with next travel
                        else:
                            print("✗ CAPTCHA auto-solve failed")
                            print("Note: This might be a false negative - checking again on next travel...")
                            print(f"{'='*60}\n")
                            # Don't wait 10 minutes in quick test mode, just continue
                            continue
                    
                    print("\nThe game has detected automated actions.")
                    print("Please visit: https://web.simple-mmo.com/i-am-not-a-bot")
                    print("Complete the verification, then restart the bot.\n")
                    print(f"{'='*60}\n")
                    return
                
                # Check if material gathering happened before travel (pre-travel check)
                material_gather_data = result.get("material_gather")
                if material_gather_data:
                    if material_gather_data.get("success"):
                        gather_exp = material_gather_data.get("exp", 0)
                        gather_gold = material_gather_data.get("gold", 0)
                        gather_items = material_gather_data.get("items", [])
                        
                        print(f"\n{'='*60}")
                        print(f"🔨 MATERIAL GATHERED (Pre-Travel)")
                        print(f"{'='*60}")
                        if gather_exp > 0:
                            print(f"  💫 +{gather_exp} EXP")
                        if gather_gold > 0:
                            print(f"  💰 +{gather_gold} gold")
                        if gather_items:
                            print(f"  🎁 +{len(gather_items)} items")
                        print(f"{'='*60}\n")
                    elif material_gather_data.get("insufficient_energy"):
                        print(f"\n⚠️  Not enough energy for gathering - skipping...\n")
                
                # Check if NPC battle occurred before travel
                npc_battle_data = result.get("npc_battle")
                if npc_battle_data:
                    print(f"\n{'='*60}")
                    print(f"⚔️  NPC BATTLE COMPLETED")
                    print(f"{'='*60}")
                    
                    # Show battle rewards
                    if isinstance(npc_battle_data, dict):
                        battle_exp = npc_battle_data.get("exp", npc_battle_data.get("experience", 0))
                        battle_gold = npc_battle_data.get("gold", npc_battle_data.get("coins", 0))
                        battle_msg = npc_battle_data.get("message", "")
                        battle_attacks = npc_battle_data.get("attacks", 0)
                        battle_damage = npc_battle_data.get("damage", 0)
                        
                        if battle_msg:
                            print(f"  💬 {battle_msg}")
                        if battle_attacks > 0:
                            print(f"  ⚔️  Attacks: {battle_attacks}")
                        if battle_damage > 0:
                            print(f"  💥 Total Damage: {battle_damage}")
                        if battle_exp > 0:
                            print(f"  💫 Battle EXP: +{battle_exp}")
                        if battle_gold > 0:
                            print(f"  💰 Battle Gold: +{battle_gold}")
                    
                    print(f"  ✅ Continuing with travel...\n")
                    print(f"{'='*60}\n")
                
                # Display results
                print(f"\n{'='*60}")
                print(f"✓ Travel #{count} completed")
                
                if parsed:
                    # Show message if it's clean (not HTML)
                    msg = parsed.get("message", "")
                    if msg and "<" not in msg:  # Not HTML
                        # Truncate very long messages
                        if len(msg) > 150:
                            msg = msg[:150] + "..."
                        print(f"  💬 {msg}")
                    
                    # Check for material gathering/salvage or event items
                    if parsed.get("material_encounter"):
                        material_session_id = parsed.get("material_session_id")
                        material_name = parsed.get("material_name") or "Material"
                        material_qty = parsed.get("material_quantity", 1)
                        
                        print(f"\n  🔨 {material_name} found! Gathering...")
                        
                        # Auto-gather the material
                        gather_result = self.salvage_material(material_session_id, material_qty, material_name)
                        
                        if gather_result.get("success"):
                            gather_exp = gather_result.get("exp", 0)
                            gather_gold = gather_result.get("gold", 0)
                            gather_items = gather_result.get("items", [])
                            
                            print(f"  ✅ Gathered successfully!")
                            if gather_exp > 0:
                                print(f"  💫 +{gather_exp} EXP")
                            if gather_gold > 0:
                                print(f"  💰 +{gather_gold} gold")
                            if gather_items:
                                print(f"  🎁 +{len(gather_items)} items")
                        else:
                            error_msg = gather_result.get('error', 'Unknown error')
                            print(f"  ⚠️  Failed to gather '{material_name}': {error_msg}")
                        print()
                    
                    # Show rewards with better detection
                    has_rewards = False
                    exp_gained = parsed.get("exp", 0)
                    gold_gained = parsed.get("gold", 0)
                    items = parsed.get("items", [])
                    
                    if exp_gained > 0:
                        current_exp = parsed.get("current_exp", 0)
                        if current_exp > 0:
                            print(f"  💫 EXP: +{exp_gained} (Current: {current_exp:,})")
                        else:
                            print(f"  💫 EXP: +{exp_gained}")
                        has_rewards = True
                    
                    if gold_gained > 0:
                        current_gold = parsed.get("current_gold", 0)
                        if current_gold > 0:
                            print(f"  💰 Gold: +{gold_gained} (Current: {current_gold:,})")
                        else:
                            print(f"  💰 Gold: +{gold_gained}")
                        has_rewards = True
                    
                    if items and len(items) > 0:
                        print(f"  🎁 Items found:")
                        for item in items[:5]:  # Limit to first 5
                            if isinstance(item, dict):
                                item_name = item.get("name", item.get("item", "Unknown"))
                                item_qty = item.get("quantity", item.get("qty", 1))
                                rarity = item.get("rarity", "")
                                if rarity:
                                    print(f"     - {item_name} x{item_qty} ({rarity})")
                                else:
                                    print(f"     - {item_name} x{item_qty}")
                            else:
                                print(f"     - {item}")
                        if len(items) > 5:
                            print(f"     ... and {len(items) - 5} more items")
                        has_rewards = True
                    
                    # Show additional info
                    if parsed.get("step_count", 0) > 0:
                        print(f"  👣 Steps: {parsed['step_count']}")
                    
                    if parsed.get("wait_time", 0) > 0:
                        wait_sec = parsed['wait_time']
                        print(f"  ⏱️  Cooldown: {wait_sec:.1f}s")
                    
                    # If no rewards detected, show raw data for debugging
                    if not has_rewards:
                        print(f"  ➡️  Moved forward (no rewards this step)")
                        # Show raw response for debugging (if debug mode enabled)
                        if self.config.get("debug_mode", False):
                            print(f"  🔍 Debug - Raw API response:")
                            import json
                            print(f"     {json.dumps(parsed.get('raw', {}), indent=6)}")
                        # Log raw data for debugging
                        self.logger.debug(f"Raw response data: {parsed.get('raw', {})}")
                
                print(f"{'='*60}\n")
            else:
                self.logger.warning(f"Travel failed: {result.get('error')}")
                # Check if we need to wait for cooldown
                if "cooldown" in str(result.get("error", "")).lower():
                    self.logger.info("Cooldown detected, waiting...")
                    self._countdown(60, "Cooldown")
                    continue
            
            # Random delay between actions
            delay = self.get_random_delay(
                self.config.get("travel_delay_min", 2),
                self.config.get("travel_delay_max", 5)
            )
            
            # Use countdown instead of plain sleep
            self._countdown(delay, "Next travel in")


def main():
    """Main function to run the bot"""
    print("=" * 60)
    print("SimpleMMO Automation Bot - Developer Testing Tool")
    print("=" * 60)
    
    # Initialize bot
    bot = SimpleMMOBot()
    
    # Auto-login using credentials from config
    print("\n[Logging in...]")
    if not bot.login():
        print("✗ Login failed. Check your credentials in config.json")
        return
    
    print("✓ Logged in successfully!")
    
    # Choose automation mode
    print("\nAutomation Options:")
    print("1. Auto Travel (continuous)")
    print("2. Single Travel (test)")
    mode = input("Select mode (1-2): ").strip()
    
    try:
        if mode == "1":
            iterations = input("Number of iterations (leave empty for infinite): ").strip()
            iterations = int(iterations) if iterations else None
            bot.auto_travel_loop(iterations)
        elif mode == "2":
            result = bot.travel()
            print(f"\nResult: {result}")
        else:
            print("Invalid mode selected")
    except KeyboardInterrupt:
        print("\n\n✓ Bot stopped by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
