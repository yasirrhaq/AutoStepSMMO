#!/usr/bin/env python3
"""
SimpleMMO Quest Runner Bot
Automatically completes quests in order from lowest to highest level
"""

import requests
import time
import json
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Optional, Any, List, Tuple
import random
import re
from bs4 import BeautifulSoup
from simplemmo_bot import SimpleMMOBot


class QuestRunner(SimpleMMOBot):
    """Bot for automating SimpleMMO quest completion"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize the quest runner"""
        super().__init__(config_file)
        self.quest_api_url = "https://web.simple-mmo.com/api/quests/perform"
        self.quests_page_url = f"{self.base_url}/quests"
        self.quest_points = None
        self.max_quest_points = None
        self.quest_points_next_regen_at = None  # Unix timestamp

        # Quest-specific config (all values fall back to sensible defaults)
        _qc = self.config.get("quest", {})
        self.quest_delay_steps_min   = _qc.get("delay_between_steps_min",  2)
        self.quest_delay_steps_max   = _qc.get("delay_between_steps_max",  4)
        self.quest_delay_quests_min  = _qc.get("delay_between_quests_min", 3)
        self.quest_delay_quests_max  = _qc.get("delay_between_quests_max", 6)
        self.quest_qp_poll_interval  = int(_qc.get("qp_poll_interval",    60))
        self.quest_error_retry_delay = _qc.get("error_retry_delay",       10)
        
        # Setup quest-specific logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('quest_runner.log'),
                logging.StreamHandler()
            ]
        )
    
    def _get_delay(self, min_delay: float, max_delay: float) -> float:
        """Return a random delay between min and max seconds"""
        return random.uniform(min_delay, max_delay)

    def extract_quest_point_info(self, page_html: str) -> Dict[str, Any]:
        """
        Extract quest point count and regen timestamp from quest page HTML.
        SimpleMMO embeds these as flat dot-notation keys inside game_data.
        Returns dict: {'quest_points': int|None, 'max_quest_points': int|None, 'next_regen_at': int|None}
        """
        info: Dict[str, Any] = {'quest_points': None, 'max_quest_points': None, 'next_regen_at': None}
        try:
            # Actual key names from SimpleMMO quest page game_data:
            #   "expedition.user.quest_points":0,"expedition.user.max_quest_points":7
            qp_m  = re.search(r'"expedition\.user\.quest_points"\s*:\s*(\d+)', page_html)
            max_m = re.search(r'"expedition\.user\.max_quest_points"\s*:\s*(\d+)', page_html)
            if qp_m:
                info['quest_points'] = int(qp_m.group(1))
            if max_m:
                info['max_quest_points'] = int(max_m.group(1))

            # Regen timestamp: not present in page HTML — we poll instead
            # (kept as None; wait_for_quest_points falls back to POLL_SECS interval)

        except Exception as e:
            self.logger.debug(f"Error extracting quest point info: {e}")

        # Cache on self
        if info['quest_points'] is not None:
            self.quest_points = info['quest_points']
        if info['max_quest_points'] is not None:
            self.max_quest_points = info['max_quest_points']
        if info['next_regen_at'] is not None:
            self.quest_points_next_regen_at = info['next_regen_at']

        return info

    def wait_for_quest_points(self):
        """
        Wait until at least 1 quest point is available, polling the quest page every POLL_SECS.
        SimpleMMO does not expose a regen timestamp in the page, so we just poll.
        """
        POLL_SECS = self.quest_qp_poll_interval

        self.logger.info("=" * 60)
        self.logger.info("Quest Points Exhausted — Waiting for Regeneration")
        self.logger.info("=" * 60)

        while True:
            # Re-fetch quest page to get fresh QP data
            try:
                response = self.session.get(self.quests_page_url, allow_redirects=True)
                page_html = response.text if response.status_code == 200 else ""
            except Exception as e:
                self.logger.warning(f"Could not fetch quest page: {e}")
                page_html = ""

            qp_info    = self.extract_quest_point_info(page_html)
            current_qp = qp_info.get('quest_points')
            max_qp     = qp_info.get('max_quest_points')

            qp_str  = str(current_qp) if current_qp is not None else "?"
            max_str = f"/{max_qp}"    if max_qp      is not None else ""
            self.logger.info(f"Quest Points: {qp_str}{max_str} — checking again in {POLL_SECS}s")

            # If we have QP, resume
            if current_qp is not None and current_qp > 0:
                self.logger.info(f"Quest points available ({current_qp}) — resuming!")
                return

            # Countdown in 10-second ticks
            for remaining in range(POLL_SECS, 0, -10):
                print(f"\r  [QP wait] Rechecking in {remaining:3d}s ...  ", end='', flush=True)
                time.sleep(min(10, remaining))
            print()

    def extract_quest_api_endpoints(self, page_html: str) -> Dict[str, str]:
        """Extract quest API endpoints from page HTML (from game_data)"""
        try:
            # Look for expedition.get_endpoint and expedition.perform_endpoint in game_data
            # Pattern: "expedition.get_endpoint":"URL","expedition.perform_endpoint":"URL"
            get_pattern = r'"expedition\.get_endpoint":"([^"]+)"'
            perform_pattern = r'"expedition\.perform_endpoint":"([^"]+)"'
            
            get_match = re.search(get_pattern, page_html)
            perform_match = re.search(perform_pattern, page_html)
            
            endpoints = {}
            
            if get_match:
                # Unescape the URL: the HTML embeds it as JSON, so \/  → /  and \uXXXX → char
                raw = get_match.group(1)
                try:
                    import json as _json
                    endpoints['get_url'] = _json.loads(f'"{raw}"')
                except Exception:
                    endpoints['get_url'] = raw.replace('\\/', '/')
                self.logger.debug(f"Found get endpoint: {endpoints['get_url'][:60]}...")
            
            if perform_match:
                raw = perform_match.group(1)
                try:
                    import json as _json
                    endpoints['perform_url'] = _json.loads(f'"{raw}"')
                except Exception:
                    endpoints['perform_url'] = raw.replace('\\/', '/')
                self.logger.debug(f"Found perform endpoint: {endpoints['perform_url'][:60]}...")
            
            if not endpoints:
                self.logger.warning("Could not extract quest API endpoints from page")
            
            return endpoints
            
        except Exception as e:
            self.logger.error(f"Error extracting API endpoints: {e}")
            return {}
    
    def get_available_quests(self) -> List[Dict[str, Any]]:
        """Fetch list of available quests from the API"""
        try:
            self.logger.info("Fetching available quests...")
            
            # First, get the quest page to extract API endpoints
            response = self.session.get(self.quests_page_url, allow_redirects=True)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch quests page: HTTP {response.status_code}")
                return []
            
            page_html = response.text

            # Extract quest point info while we have the page HTML
            self.extract_quest_point_info(page_html)

            # Extract API endpoints from page
            endpoints = self.extract_quest_api_endpoints(page_html)
            
            if not endpoints.get('get_url'):
                self.logger.error("Could not find quest API GET endpoint")
                return []
            
            # Now fetch the actual quest data from the API
            get_url = endpoints['get_url']
            perform_url = endpoints.get('perform_url', '')
            
            self.logger.info("Fetching quest data from API...")
            self.logger.info(f"Using POST method to: {get_url[:80]}...")
            
            # The API requires POST with CSRF token + Bearer auth
            headers = {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-XSRF-TOKEN': self.csrf_token,
                'Referer': 'https://web.simple-mmo.com/quests',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            # Add Bearer token (required by the signed API endpoint)
            if self.api_token:
                headers['Authorization'] = f'Bearer {self.api_token}'
            
            # POST data with CSRF token
            data = {'_token': self.csrf_token}
            
            # Use POST to fetch quest data
            api_response = self.session.post(get_url, headers=headers, data=data)
            
            if api_response.status_code != 200:
                self.logger.error(f"Failed to fetch quest API: HTTP {api_response.status_code}")
                self.logger.error(f"Response: {api_response.text[:500]}")
                # Check if signature expired
                if 'expired' in api_response.text.lower() or 'signature' in api_response.text.lower():
                    self.logger.error("Signed URL may have expired. Try refreshing the quest page.")
                return []
            
            # Parse JSON response
            api_data = api_response.json()
            
            # The response should contain expedition data
            expeditions = api_data.get('expeditions', api_data.get('data', []))
            
            if not expeditions:
                self.logger.warning("No expeditions found in API response")
                self.logger.debug(f"API response keys: {list(api_data.keys())}")
                return []
            
            self.logger.info(f"Found {len(expeditions)} expeditions from API")

            # Log raw field names from first expedition to help diagnose level field
            if expeditions:
                first_exp = expeditions[0]
                self.logger.debug(f"First expedition raw keys: {list(first_exp.keys())}")
                level_candidates = {k: v for k, v in first_exp.items() if 'level' in k.lower()}
                if level_candidates:
                    self.logger.info(f"Level-related fields in API: {level_candidates}")
                else:
                    self.logger.warning("No 'level' fields found in expedition data — level sorting will use ID as tiebreaker")
            
            # Parse expedition data into quest format
            quests = []
            for exp in expeditions:
                quest_data = {
                    'id': exp.get('id'),
                    'title': exp.get('title', exp.get('name', 'Unknown')),
                    'level_required': (
                        exp.get('level_required')
                        or exp.get('min_level')
                        or exp.get('level')
                        or exp.get('required_level')
                        or exp.get('req_level')
                        or exp.get('level_req')
                        or exp.get('min_level_required')
                        or exp.get('expedition_level')
                        or None
                    ),
                    'image_url': exp.get('image_url', ''),
                    'is_completed': exp.get('is_completed', False),
                    'remaining': exp.get('amount_to_complete', 0) - exp.get('amount_completed', exp.get('completed_amount', 0)),
                    'experience': exp.get('experience', 0),
                    'gold': exp.get('gold', 0),
                    'success_chance': int(exp.get('success_chance', exp.get('chance', exp.get('success_rate', 100))) or 100),
                    'perform_url': perform_url,
                    'api_endpoints': endpoints
                }
                
                # Only include if quest ID and title exist
                if quest_data['id'] and quest_data['title']:
                    quests.append(quest_data)
                    self.logger.debug(f"Parsed quest: {quest_data['title']} (ID: {quest_data['id']}, Level: {quest_data['level_required']}, Completed: {quest_data['is_completed']})")
            
            self.logger.info(f"Successfully parsed {len(quests)} quests")
            
            # Fix success rate logic: higher-level quests cannot have better success rate
            # than lower-level quests. Cap each quest's success rate to the maximum
            # success rate seen at all lower levels.
            quests.sort(key=lambda q: (
                int(str(q.get('level_required', 999999)).replace(',', '')) 
                if q.get('level_required') else 999999,
                q.get('id', 999999)
            ))
            
            max_success_rate_seen = 100
            for quest in quests:
                current_rate = quest.get('success_chance', 100)
                # Cap success rate to the maximum seen at lower levels
                if current_rate > max_success_rate_seen:
                    self.logger.debug(
                        f"Adjusting success rate for '{quest['title']}' (Lvl {quest.get('level_required', '?')}): "
                        f"{current_rate}% -> {max_success_rate_seen}% (capped by lower-level quest)"
                    )
                    quest['success_chance'] = max_success_rate_seen
                else:
                    max_success_rate_seen = current_rate
            
            return quests
            
        except Exception as e:
            self.logger.error(f"Error fetching quests: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return []
    
    def get_incomplete_quests(self) -> List[Dict[str, Any]]:
        """Get list of incomplete quests sorted by level"""
        all_quests = self.get_available_quests()
        
        # Filter incomplete quests that still have steps remaining
        incomplete = [
            q for q in all_quests
            if not q.get('is_completed', False) and q.get('remaining', 0) > 0
        ]
        
        # Sort by level requirement (lowest first) — parse comma-formatted numbers like "1,001"
        # Secondary sort key: quest id (lower id = older quest = likely lower level)
        def parse_level(q):
            try:
                val = q.get('level_required')
                if val is None:
                    return 999999  # treat missing level as highest (sort last)
                return int(str(val).replace(',', ''))
            except (ValueError, TypeError):
                return 999999

        def sort_key(q):
            try:
                quest_id = int(q.get('id', 999999))
            except (ValueError, TypeError):
                quest_id = 999999
            return (parse_level(q), quest_id)

        incomplete.sort(key=sort_key)
        
        self.logger.info(f"Found {len(incomplete)} incomplete quests (sorted by level):")
        for quest in incomplete:
            self.logger.info(
                f"  [{parse_level(quest):>6}] {quest['title']} "
                f"(ID={quest.get('id')}, Remaining={quest.get('remaining')}, "
                f"Completed={quest.get('is_completed')})"
            )

        # Sanity-check: log the chosen quest clearly
        if incomplete:
            first = incomplete[0]
            self.logger.info(
                f"[SORT CHECK] Lowest = '{first['title']}' | "
                f"Level raw={first.get('level_required')} parsed={parse_level(first)} | "
                f"ID={first.get('id')} | Remaining={first.get('remaining')} | "
                f"Completed={first.get('is_completed')}"
            )
        
        return incomplete
    
    def perform_quest(self, quest_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform a quest action
        
        Args:
            quest_data: Quest data dictionary containing perform_url and expedition id
        
        Returns:
            Dict with quest result data
        """
        try:
            # Get the perform URL from quest data
            api_url = quest_data.get('perform_url') if quest_data else None
            
            if not api_url:
                self.logger.error("No perform URL provided in quest data")
                return {"success": False, "error": "Missing perform URL"}
            
            self.logger.info(
                f"Performing quest: '{quest_data.get('title', 'Unknown')}' "
                f"| expedition_id={quest_data.get('id')} "
                f"| level={quest_data.get('level_required')}"
            )
            self.logger.debug(f"Using API URL: {api_url[:80]}...")
            
            headers = {
                'X-XSRF-TOKEN': self.csrf_token,
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'Accept': 'application/json',
                'Origin': 'https://web.simple-mmo.com',
                'Referer': 'https://web.simple-mmo.com/quests',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }
            
            if self.api_token:
                headers['Authorization'] = f'Bearer {self.api_token}'
            
            # Form data - expedition_id and quantity=1 are both required
            form_data = {
                'expedition_id': quest_data['id'],
                'quantity': 1,
            }
            
            response = self.session.post(api_url, headers=headers, data=form_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Parse quest results
                status = result.get('status', 'unknown')
                message = result.get('message', '')
                gold = result.get('gold', 0)
                exp = result.get('experience', 0)
                
                self.logger.info(f"[OK] Quest result - Status: {status}")
                if message:
                    # Truncate long messages
                    if len(message) > 150:
                        self.logger.info(f"Message: {message[:150]}...")
                    else:
                        self.logger.info(f"Message: {message}")

                # Rewards: prefer values from API response, fall back to expedition data
                if not gold and quest_data:
                    gold = quest_data.get('gold', 0)
                if not exp:
                    exp = result.get('exp', 0)  # some APIs use 'exp'
                if not exp and quest_data:
                    exp = quest_data.get('experience', 0)

                # Ensure exp and gold are integers for formatting (may be strings from API)
                try:
                    exp_int = int(str(exp).replace(',', ''))
                except (ValueError, TypeError):
                    exp_int = 0
                try:
                    gold_int = int(str(gold).replace(',', ''))
                except (ValueError, TypeError):
                    gold_int = 0

                self.logger.info(f"Earned: {exp_int:,} EXP | {gold_int:,} Gold")
                
                return {
                    "success": True,
                    "status": status,
                    "message": message,
                    "gold": gold,
                    "exp": exp,
                    "data": result
                }
                
            elif response.status_code == 400:
                try:
                    err_data = response.json()
                    msg = err_data.get('message', '')
                except Exception:
                    msg = response.text[:200]
                self.logger.error(f"HTTP 400 - {msg}")
                msg_lower = msg.lower()
                if 'quest point' in msg_lower or 'not enough' in msg_lower:
                    return {"success": False, "error": "No quest points", "should_stop": True, "message": msg}
                elif 'slow down' in msg_lower or 'too fast' in msg_lower:
                    return {"success": False, "error": "Cooldown", "retry_after": 60, "message": msg}
                else:
                    return {"success": False, "error": f"HTTP 400: {msg}"}
            elif response.status_code == 429:
                return {"success": False, "error": "Rate limited / Cooldown"}
            elif response.status_code == 403:
                self.logger.error("HTTP 403 - Session may have expired")
                return {"success": False, "error": "Session expired"}
            else:
                self.logger.error(f"HTTP {response.status_code} - Response: {response.text[:200]}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Quest API error: {e}")
            return {"success": False, "error": str(e)}
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse quest response: {e}")
            return {"success": False, "error": "Invalid JSON response"}
    
    def auto_quest_loop(self, max_quests: int = None,
                         priority_quests: List[Tuple[Dict[str, Any], int]] = None,
                         direction: str = 'lowest'):
        """
        Automatically complete quests in order.

        Args:
            max_quests:      Maximum number of quests to fully complete (None = unlimited)
            priority_quests: Optional list of (quest_dict, times) to run sequentially
                             before falling into the normal lowest-level loop
            direction:       'lowest' (default) or 'highest' — controls which end of the
                             incomplete list the normal loop starts from. In both cases
                             the bot skips quests with <100% success rate until it finds
                             one that is 100%, only falling back to a non-100% quest if
                             none exist at all.
        """
        if not self.logged_in:
            self.logger.error("Not logged in - cannot run quest loop")
            return
        
        self.logger.info("=" * 60)
        self.logger.info("Starting Auto-Quest Loop")
        self.logger.info("=" * 60)

        completed_count = 0
        total_gold = 0
        total_exp = 0
        quest_steps_done = 0
        quest_progress = {}  # {title: {'done': N, 'total': N, 'remaining': N, 'id': id}}
        # Also store on self so KeyboardInterrupt in main() can still print them
        self._session_completed = 0
        self._session_gold = 0
        self._session_exp = 0
        self._session_steps = 0
        self._session_quest_progress = {}

        # ── Priority quests: run each N times before the normal loop ─────────
        for _pq_num, (_pquest, _ptimes) in enumerate(priority_quests or [], start=1):
            if _ptimes <= 0:
                continue
            _ptitle = _pquest['title']
            _total_pq = len(priority_quests)
            print("\n" + "="*60)
            print(f"  Priority Quest {_pq_num}/{_total_pq}: {_ptitle}")
            print(f"  Running {_ptimes} time(s)")
            print("="*60)
            if _ptitle not in quest_progress:
                quest_progress[_ptitle] = {
                    'done': 0, 'total': _ptimes,
                    'remaining': _ptimes, 'id': _pquest.get('id')
                }
            self._session_quest_progress = dict(quest_progress)
            _p_done = 0
            while _p_done < _ptimes:
                result = self.perform_quest(_pquest)
                if result.get('success'):
                    _p_done += 1
                    total_gold += result.get('gold', 0)
                    total_exp += result.get('exp', 0)
                    quest_steps_done += 1
                    quest_progress[_ptitle]['done'] = quest_progress[_ptitle].get('done', 0) + 1
                    quest_progress[_ptitle]['remaining'] = _ptimes - _p_done
                    self._session_gold = total_gold
                    self._session_exp = total_exp
                    self._session_steps = quest_steps_done
                    self._session_quest_progress = dict(quest_progress)
                    self.logger.info(f"Priority quest {_pq_num}/{_total_pq} progress: {_p_done}/{_ptimes}")
                    if _p_done < _ptimes:
                        delay = self._get_delay(self.quest_delay_steps_min, self.quest_delay_steps_max)
                        self.logger.info(f"Waiting {delay:.1f}s...")
                        time.sleep(delay)
                else:
                    error = result.get('error', 'Unknown error')
                    if result.get('should_stop'):
                        self.logger.warning("Out of quest points — waiting for regen...")
                        self.wait_for_quest_points()
                    elif 'session expired' in error.lower():
                        self.logger.error("Session expired — stopping.")
                        return
                    elif 'rate limit' in error.lower() or error == 'Cooldown':
                        time.sleep(result.get('retry_after', 30))
                    else:
                        time.sleep(self.quest_error_retry_delay)
            print("\n" + "="*60)
            print(f"  Priority Quest {_pq_num}/{_total_pq} Done: {_ptitle}")
            print(f"  Performed {_p_done} time(s)")
            print(f"  Session EXP so far : {total_exp:,}")
            print(f"  Session Gold so far: {total_gold:,}")
            print("="*60)
            if _pq_num < _total_pq:
                delay = self._get_delay(self.quest_delay_quests_min, self.quest_delay_quests_max)
                print(f"  Next priority quest in {delay:.1f}s...\n")
                time.sleep(delay)
            else:
                print("  All priority quests done — resuming normal quest loop...\n")

        # ── Normal quest loop ────────────────────────────────────────────────
        while True:
            # Check if we've hit the max quest limit
            if max_quests and completed_count >= max_quests:
                self.logger.info(f"Reached maximum quest limit ({max_quests})")
                break
            
            # Get incomplete quests
            incomplete_quests = self.get_incomplete_quests()

            if not incomplete_quests:
                self.logger.info("No more incomplete quests available!")
                break

            # Pick based on direction, preferring quests with 100% success rate
            if direction == 'highest':
                search_order = list(reversed(incomplete_quests))
            else:
                search_order = list(incomplete_quests)
            current_quest = next(
                (q for q in search_order if q.get('success_chance', 100) >= 100),
                search_order[0]  # fallback: first in chosen direction if none are 100%
            )
            _sc = current_quest.get('success_chance', 100)
            if _sc < 100:
                self.logger.warning(
                    f"No 100% success quest found in '{direction}' direction — "
                    f"picking '{current_quest['title']}' ({_sc}% chance) as fallback"
                )
            
            self.logger.info("")
            self.logger.info("=" * 60)
            self.logger.info(f"Current Quest: {current_quest['title']}")
            self.logger.info(f"Level Requirement: {current_quest.get('level_required', '?')}")
            self.logger.info(f"Remaining: {current_quest.get('remaining', '?')}")
            self.logger.info("=" * 60)
            
            # Perform the quest multiple times until completion
            quest_attempts = 0
            quest_remaining = current_quest.get('remaining', 1)
            quest_title = current_quest['title']
            quest_id = current_quest.get('id', '?')
            # Init progress entry for this quest (preserve if already started)
            if quest_title not in quest_progress:
                quest_progress[quest_title] = {
                    'done': 0,
                    'total': quest_remaining,
                    'remaining': quest_remaining,
                    'id': quest_id
                }
            self._session_quest_progress = dict(quest_progress)

            while quest_remaining > 0:
                quest_attempts += 1
                
                self.logger.info(f"\nAttempt {quest_attempts} - Performing quest...")
                
                # Perform quest action
                result = self.perform_quest(current_quest)
                
                if result.get('success'):
                    # Update counters
                    total_gold += result.get('gold', 0)
                    total_exp += result.get('exp', 0)
                    quest_remaining -= 1
                    quest_steps_done += 1
                    quest_progress[quest_title]['done'] += 1
                    quest_progress[quest_title]['remaining'] = quest_remaining
                    # Keep self in sync for interrupt-safe stats
                    self._session_gold = total_gold
                    self._session_exp = total_exp
                    self._session_steps = quest_steps_done
                    self._session_quest_progress = dict(quest_progress)
                    
                    self.logger.info(f"Quest progress: {quest_remaining} remaining")
                    
                    # Wait between attempts
                    delay = self._get_delay(
                        self.quest_delay_steps_min,
                        self.quest_delay_steps_max
                    )
                    
                    if quest_remaining > 0:
                        self.logger.info(f"Waiting {delay:.1f}s before next attempt...")
                        time.sleep(delay)
                    
                else:
                    error = result.get('error', 'Unknown error')
                    self.logger.error(f"Quest failed: {error}")
                    
                    # Handle different error types
                    if result.get('should_stop'):
                        self.logger.warning("Out of quest points — pausing until regen...")
                        self.wait_for_quest_points()
                        # Break inner loop; outer loop will re-fetch quests with fresh remaining count
                        break
                    elif 'session expired' in error.lower():
                        self.logger.error("Session expired - please restart with fresh tokens")
                        return
                    elif 'rate limit' in error.lower() or error == 'Cooldown':
                        wait = result.get('retry_after', 30)
                        self.logger.warning(f"Rate limited / cooldown - waiting {wait} seconds...")
                        time.sleep(wait)
                    else:
                        self.logger.warning(f"Waiting {self.quest_error_retry_delay}s before retry...")
                        time.sleep(self.quest_error_retry_delay)
            
            # Quest completed — only if inner loop finished normally (not broken by QP wait)
            if quest_remaining == 0:
                completed_count += 1
                self._session_completed = completed_count
                _q_steps = quest_progress[quest_title]['done']
                print("\n" + "="*60)
                print(f"  Quest Completed: {quest_title}")
                print("="*60)
                print(f"  Attempts (this quest)   : {_q_steps}")
                print(f"  Quests completed        : {completed_count}")
                print(f"  Session EXP so far      : {total_exp:,}")
                print(f"  Session Gold so far     : {total_gold:,}")
                print("="*60)

                # Wait before moving to next quest
                delay = self._get_delay(
                    self.quest_delay_quests_min,
                    self.quest_delay_quests_max
                )
                print(f"  Moving to next quest in {delay:.1f}s...\n")
                time.sleep(delay)
        
        # Final summary
        print("\n" + "="*60)
        print("  Quest Session Complete!")
        print("="*60)
        print(f"  Quests completed : {completed_count}")
        print(f"  Total EXP        : {total_exp:,}")
        print(f"  Total Gold       : {total_gold:,}")
        if quest_progress:
            print("-"*60)
            for _title, _info in quest_progress.items():
                _icon = "OK" if _info['remaining'] == 0 else "->"
                _status = "completed" if _info['remaining'] == 0 else f"{_info['done']}/{_info['total']} done, {_info['remaining']} left"
                print(f"   [{_icon}] {_title}: {_status}")
        print("="*60)


def main():
    """Main entry point"""
    print("=" * 60)
    print("SimpleMMO Auto-Quest Runner")
    print("=" * 60)
    print()
    
    # Initialize bot
    bot = QuestRunner("config.json")
    
    # Login
    print("Logging in...")
    
    # Try session token first
    session_token = bot.config.get("session_token", "")
    xsrf_token = bot.config.get("xsrf_token", "")
    
    if session_token:
        print("Using session token from config...")
        if not bot.login_with_session_token(session_token, xsrf_token):
            print("Failed to login with session token")
            return
    else:
        # Try email/password
        email = bot.config.get("email", "")
        password = bot.config.get("password", "")
        
        if email and password:
            print("Using email/password from config...")
            if not bot.login(email, password):
                print("Failed to login with email/password")
                return
        else:
            print("Error: No login credentials found in config.json")
            print("Please add either:")
            print("  - session_token (and optionally xsrf_token)")
            print("  - email and password")
            return
    
    print("[OK] Login successful")
    print()

    # ── Interactive quest picker ─────────────────────────────────────────────
    priority_quests: List[Tuple[Dict[str, Any], int]] = []

    print("Fetching quest list...")
    incomplete = bot.get_incomplete_quests()

    if incomplete:
        print()
        print("=" * 60)
        print("  Available Incomplete Quests")
        print("=" * 60)
        for i, q in enumerate(incomplete, 1):
            lvl = q.get('level_required', '?')
            rem = q.get('remaining', '?')
            sc  = q.get('success_chance', 100)
            sc_tag = f"{sc}%" if sc < 100 else "100%"
            sc_label = f"  \033[91m[{sc_tag}]\033[0m" if sc < 100 else f"  \033[92m[{sc_tag}]\033[0m"
            print(f"  {i:>3}. [Lvl {lvl:>6}] {q['title']}  (remaining: {rem}){sc_label}")
        print("=" * 60)
        print()
        print("  You can queue multiple quests to run in order before the normal loop.")
        print("  For each slot: type a NUMBER to pick a quest, or press Enter to stop")
        print("  adding quests and start the bot.")
        print()

        slot = 1
        while True:
            choice = input(f"  Quest #{slot} (Enter to start bot): ").strip()
            if not choice:
                break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(incomplete):
                    picked = incomplete[idx]
                    times_str = input(
                        f"  How many times to run '{picked['title']}'? "
                        f"(remaining: {picked.get('remaining', '?')}, Enter = 1): "
                    ).strip()
                    times = int(times_str) if times_str.isdigit() and int(times_str) > 0 else 1
                    priority_quests.append((picked, times))
                    print(f"  → Added: '{picked['title']}' x{times}")
                    print()
                    slot += 1
                else:
                    print(f"  Invalid number, try 1-{len(incomplete)}.")
            except ValueError:
                print("  Please enter a valid number.")

        if priority_quests:
            print()
            print("  Queue:")
            for n, (q, t) in enumerate(priority_quests, 1):
                sc = q.get('success_chance', 100)
                sc_str = f" ({sc}% success)" if sc < 100 else ""
                print(f"    {n}. {q['title']}  x{t}{sc_str}")
            print("  After the queue finishes, the bot will continue with the")
            print("  auto-loop using the direction you choose below.")
            print()
        else:
            print("  No quests queued.\n")

        # ── Direction prompt ──────────────────────────────────────────────────
        print("  Normal loop direction (after queue, or immediately if no queue):")
        print("    [L] Lowest level first — skips quests below 100% success rate")
        print("    [H] Highest level first — skips quests below 100% success rate,")
        print("        works downward looking for the highest 100% quest")
        print()
        dir_choice = input("  Direction (L/H, Enter = lowest): ").strip().lower()
        direction = 'highest' if dir_choice == 'h' else 'lowest'
        if direction == 'highest':
            print("  \u2192 Highest-level 100% quests first, working downward.\n")
        else:
            print("  \u2192 Lowest-level quests first (default).\n")
    else:
        print("No incomplete quests found.")
        return

    # ── Signal handlers ──────────────────────────────────────────────────────
    def _handle_shutdown(sig, frame):
        print("\n\nShutdown signal received — stopping quest bot cleanly...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_shutdown)
    try:
        signal.signal(signal.SIGBREAK, _handle_shutdown)  # Windows: Ctrl+Close / window X
    except (AttributeError, OSError):
        pass  # SIGBREAK not available on non-Windows

    # ── Auto-restart loop ────────────────────────────────────────────────────
    _restart_count = 0

    while True:
        if _restart_count > 0:
            print(f"\n{'='*60}")
            print(f"  Auto-restarting bot (restart #{_restart_count})...")
            print(f"{'='*60}\n")
            time.sleep(2)

        # Start quest loop
        try:
            bot.auto_quest_loop(priority_quests=priority_quests, direction=direction)
            # If loop completes normally (no more quests), exit
            break

        except KeyboardInterrupt:
            _completed  = getattr(bot, '_session_completed', 0)
            _steps      = getattr(bot, '_session_steps', 0)
            _exp        = getattr(bot, '_session_exp', 0)
            _gold       = getattr(bot, '_session_gold', 0)
            _qp         = getattr(bot, '_session_quest_progress', {})
            print("\n\n" + "="*60)
            print("Quest Runner stopped.")
            print("="*60)
            print(f"  Quests fully completed : {_completed}")
            print(f"  Total attempts         : {_steps}")
            print(f"  Total EXP              : {_exp:,}")
            print(f"  Total Gold             : {_gold:,}")
            if _qp:
                print("-"*60)
                print("  Quest Progress:")
                for _title, _info in _qp.items():
                    _done      = _info['done']
                    _total     = _info['total']
                    _remaining = _info['remaining']
                    _icon      = "OK" if _remaining == 0 else "->"
                    _status    = "completed" if _remaining == 0 else f"{_done}/{_total} done, {_remaining} left"
                    print(f"   [{_icon}] {_title}: {_status}")
            print("="*60)

            # Ask user to restart or exit
            restart = input("\n Press Enter to restart, or C to close: ").strip().lower()
            if restart == 'c':
                print("\nBot stopped gracefully. Goodbye!")
                break
            else:
                _restart_count += 1
                # Re-login to refresh session
                try:
                    bot.login()
                except Exception as e:
                    print(f"\nRe-login failed: {e}")
                    print("Please restart manually with fresh credentials.")
                    break

        except SystemExit:
            break  # clean shutdown via signal handler

        except Exception as e:
            print(f"\n\n{'='*60}")
            print(f"  ERROR: {e}")
            print(f"{'='*60}")
            bot.logger.error(f"Fatal error: {e}", exc_info=True)

            # Show session stats before restart
            _completed  = getattr(bot, '_session_completed', 0)
            _steps      = getattr(bot, '_session_steps', 0)
            _exp        = getattr(bot, '_session_exp', 0)
            _gold       = getattr(bot, '_session_gold', 0)
            _qp         = getattr(bot, '_session_quest_progress', {})

            if _steps > 0 or _completed > 0:
                print("\n" + "="*60)
                print("  Session Stats (before error)")
                print("="*60)
                print(f"  Quests completed : {_completed}")
                print(f"  Total attempts   : {_steps}")
                print(f"  Total EXP        : {_exp:,}")
                print(f"  Total Gold       : {_gold:,}")
                if _qp:
                    print("-"*60)
                    print("  Quest Progress:")
                    for _title, _info in _qp.items():
                        _done      = _info['done']
                        _total     = _info['total']
                        _remaining = _info['remaining']
                        _icon      = "OK" if _remaining == 0 else "->"
                        _status    = "completed" if _remaining == 0 else f"{_done}/{_total} done, {_remaining} left"
                        print(f"   [{_icon}] {_title}: {_status}")
                print("="*60)

            # Ask user to restart or exit
            restart = input("\n Press Enter to restart, or C to close: ").strip().lower()
            if restart == 'c':
                print("\nBot stopped. Goodbye!")
                break
            else:
                _restart_count += 1
                # Re-login to refresh session
                try:
                    bot.login()
                except Exception as login_err:
                    print(f"\nRe-login failed: {login_err}")
                    print("Please restart manually with fresh credentials.")
                    break


if __name__ == "__main__":
    main()
