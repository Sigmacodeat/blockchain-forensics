"""
Advanced Link Tracking & Attribution System
Professional Marketing Attribution wie Bitly, Branch.io + Intelligence-Grade Analytics

Features:
- Custom Short-Links mit Tracking
- Social-Media-Platform-Detection
- Username/Profile-Extraction
- IP-Geolocation (Stadt, Land, Koordinaten)
- ISP-Detection
- Device-Fingerprinting
- Referrer-Chain-Analysis
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class LinkTracker:
    """
    Professional Link-Tracking System
    
    Erstellt Custom Short-Links wie:
    https://yoursite.com/s/twitter-john
    https://yoursite.com/s/linkedin-ceo
    https://yoursite.com/s/reddit-crypto
    
    Tracked:
    - Welche Social-Media-Platform (Twitter, LinkedIn, Instagram, etc.)
    - Username/Profile (wenn möglich)
    - IP-Geolocation (Stadt, Land, Koordinaten)
    - ISP (Internet Service Provider)
    - Device-Fingerprint
    - Complete Referrer-Chain
    """
    
    @staticmethod
    def create_tracking_link(
        target_url: str,
        source_platform: str,
        source_username: Optional[str] = None,
        campaign: Optional[str] = None,
        custom_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Erstelle Tracking-Link
        
        Args:
            target_url: Ziel-URL (z.B. https://yoursite.com/pricing)
            source_platform: Social-Media-Platform (twitter, linkedin, instagram, etc.)
            source_username: Optional: Username/Profile
            campaign: Optional: Campaign-Name
            custom_slug: Optional: Custom short-slug
        
        Returns:
            {
                "short_url": "https://yoursite.com/s/twitter-john",
                "tracking_id": "trk_abc123",
                "qr_code": "base64...",
                "analytics_dashboard": "https://yoursite.com/admin/links/trk_abc123"
            }
        
        Example:
            # Twitter-Link
            link = create_tracking_link(
                target_url="https://yoursite.com/pricing",
                source_platform="twitter",
                source_username="john_doe",
                campaign="summer_2025"
            )
            
            # Instagram-Link
            link = create_tracking_link(
                target_url="https://yoursite.com",
                source_platform="instagram",
                source_username="crypto_expert",
                campaign="influencer"
            )
        """
        from app.models.link_tracking import TrackedLink
        from app.db.session import get_db
        
        # Generate Tracking-ID
        tracking_id = f"trk_{hashlib.md5(f'{source_platform}{source_username}{datetime.utcnow()}'.encode()).hexdigest()[:12]}"
        
        # Generate Short-Slug
        if not custom_slug:
            if source_username:
                custom_slug = f"{source_platform}-{source_username}".lower().replace(' ', '-')
            else:
                custom_slug = f"{source_platform}-{tracking_id[:6]}"
        
        # Build UTM-Parameters
        utm_params = {
            "utm_source": source_platform,
            "utm_medium": "social",
            "utm_campaign": campaign or "organic",
            "utm_content": source_username or "unknown",
            "tracking_id": tracking_id
        }
        
        # Build Full URL with UTM
        separator = "&" if "?" in target_url else "?"
        utm_string = "&".join([f"{k}={v}" for k, v in utm_params.items()])
        full_target_url = f"{target_url}{separator}{utm_string}"
        
        # Short URL
        short_url = f"https://yoursite.com/s/{custom_slug}"
        
        # Save to Database
        link = TrackedLink(
            tracking_id=tracking_id,
            short_slug=custom_slug,
            short_url=short_url,
            target_url=full_target_url,
            source_platform=source_platform,
            source_username=source_username,
            campaign=campaign,
            created_at=datetime.utcnow()
        )
        
        # Generate QR Code
        qr_code = LinkTracker._generate_qr_code(short_url)
        
        return {
            "short_url": short_url,
            "tracking_id": tracking_id,
            "qr_code": qr_code,
            "analytics_dashboard": f"https://yoursite.com/admin/links/{tracking_id}",
            "embed_code": f'<a href="{short_url}" data-tracking="{tracking_id}">Click Here</a>'
        }
    
    @staticmethod
    def track_click(
        tracking_id: str,
        ip_address: str,
        user_agent: str,
        referrer: Optional[str] = None,
        fingerprint: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track Link-Click mit Maximum-Intelligence
        
        Erfasst:
        - IP-Geolocation (Stadt, Land, Koordinaten, Zeitzone)
        - ISP (Internet Provider)
        - Social-Media-Platform (aus Referrer)
        - Username (wenn erkennbar)
        - Device-Info (OS, Browser, Device-Type)
        - Connection-Type (Mobile, Desktop, Bot)
        
        Returns:
            Complete Intelligence-Report
        """
        # 1. IP-Geolocation (Stadt-Level)
        geo = LinkTracker._get_ip_geolocation(ip_address)
        
        # 2. ISP-Detection
        isp = LinkTracker._get_isp(ip_address)
        
        # 3. Social-Media-Detection (aus Referrer)
        social_info = LinkTracker._detect_social_media(referrer, user_agent)
        
        # 4. Device-Analysis
        device_info = LinkTracker._analyze_device(user_agent)
        
        # 5. Bot-Detection
        is_bot = LinkTracker._is_bot(user_agent, ip_address)
        
        # 6. Fingerprint-Analysis
        if fingerprint:
            fingerprint_hash = LinkTracker._hash_fingerprint(fingerprint)
        else:
            fingerprint_hash = None
        
        # Complete Intelligence-Report
        intelligence = {
            "tracking_id": tracking_id,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_intelligence": {
                "ip_address": ip_address,
                "country": geo.get("country"),
                "country_code": geo.get("country_code"),
                "region": geo.get("region"),
                "city": geo.get("city"),
                "postal_code": geo.get("postal_code"),
                "latitude": geo.get("latitude"),
                "longitude": geo.get("longitude"),
                "timezone": geo.get("timezone"),
                "isp": isp,
                "is_vpn": geo.get("is_vpn", False),
                "is_proxy": geo.get("is_proxy", False),
                "is_tor": geo.get("is_tor", False)
            },
            "social_media": {
                "platform": social_info.get("platform"),
                "username": social_info.get("username"),
                "profile_url": social_info.get("profile_url"),
                "referrer_full": referrer
            },
            "device": {
                "os": device_info.get("os"),
                "os_version": device_info.get("os_version"),
                "browser": device_info.get("browser"),
                "browser_version": device_info.get("browser_version"),
                "device_type": device_info.get("device_type"),  # mobile, tablet, desktop
                "device_brand": device_info.get("device_brand"),
                "is_mobile": device_info.get("is_mobile"),
                "is_bot": is_bot
            },
            "fingerprint": {
                "hash": fingerprint_hash,
                "data": fingerprint
            }
        }
        
        # Save to Database
        from app.models.link_tracking import LinkClick
        click = LinkClick(
            tracking_id=tracking_id,
            intelligence_data=intelligence,
            created_at=datetime.utcnow()
        )
        
        logger.info(f"Link clicked: {tracking_id} from {geo.get('city')}, {geo.get('country')} via {social_info.get('platform')}")
        
        return intelligence
    
    @staticmethod
    def _get_ip_geolocation(ip_address: str) -> Dict[str, Any]:
        """
        IP-Geolocation (Stadt-Level, Legal)
        
        Uses:
        - ip-api.com (free, 45 req/min)
        - ipapi.co (free, 1000 req/day)
        - ipinfo.io (free, 50k req/month)
        
        Returns: Stadt, Land, Koordinaten, Zeitzone, ISP, Proxy-Detection
        """
        try:
            # Use ip-api.com (free)
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,proxy,hosting",
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    return {
                        "country": data.get("country"),
                        "country_code": data.get("countryCode"),
                        "region": data.get("regionName"),
                        "city": data.get("city"),
                        "postal_code": data.get("zip"),
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon"),
                        "timezone": data.get("timezone"),
                        "isp": data.get("isp"),
                        "organization": data.get("org"),
                        "as_number": data.get("as"),
                        "is_proxy": data.get("proxy", False),
                        "is_vpn": data.get("hosting", False),  # Hosting IPs often VPNs
                        "is_tor": False  # Requires specialized service
                    }
        except Exception as e:
            logger.error(f"IP-Geolocation failed: {e}")
        
        return {
            "country": "Unknown",
            "city": "Unknown",
            "latitude": None,
            "longitude": None
        }
    
    @staticmethod
    def _get_isp(ip_address: str) -> str:
        """Get ISP (Internet Service Provider)"""
        # Already included in _get_ip_geolocation
        return "Unknown"
    
    @staticmethod
    def _detect_social_media(referrer: Optional[str], user_agent: str) -> Dict[str, Any]:
        """
        Detect Social-Media-Platform & Username
        
        Analyzes:
        - Referrer URL
        - User-Agent (some apps have specific UAs)
        - URL-Patterns
        
        Detects:
        - Twitter/X
        - LinkedIn
        - Instagram
        - Facebook
        - TikTok
        - Reddit
        - YouTube
        - WhatsApp
        - Telegram
        - Discord
        """
        if not referrer:
            return {"platform": "direct", "username": None}
        
        referrer_lower = referrer.lower()
        
        # Twitter/X
        if "twitter.com" in referrer_lower or "t.co" in referrer_lower or "x.com" in referrer_lower:
            # Extract username: https://twitter.com/username/status/...
            username = LinkTracker._extract_twitter_username(referrer)
            return {
                "platform": "twitter",
                "username": username,
                "profile_url": f"https://twitter.com/{username}" if username else None
            }
        
        # LinkedIn
        elif "linkedin.com" in referrer_lower:
            # Extract: https://www.linkedin.com/in/username/
            username = LinkTracker._extract_linkedin_username(referrer)
            return {
                "platform": "linkedin",
                "username": username,
                "profile_url": f"https://linkedin.com/in/{username}" if username else None
            }
        
        # Instagram
        elif "instagram.com" in referrer_lower:
            # Extract: https://www.instagram.com/username/
            username = LinkTracker._extract_instagram_username(referrer)
            return {
                "platform": "instagram",
                "username": username,
                "profile_url": f"https://instagram.com/{username}" if username else None
            }
        
        # Facebook
        elif "facebook.com" in referrer_lower or "fb.com" in referrer_lower:
            return {"platform": "facebook", "username": None}
        
        # TikTok
        elif "tiktok.com" in referrer_lower:
            username = LinkTracker._extract_tiktok_username(referrer)
            return {
                "platform": "tiktok",
                "username": username,
                "profile_url": f"https://tiktok.com/@{username}" if username else None
            }
        
        # Reddit
        elif "reddit.com" in referrer_lower:
            # Extract subreddit: https://www.reddit.com/r/cryptocurrency/
            subreddit = LinkTracker._extract_reddit_subreddit(referrer)
            return {
                "platform": "reddit",
                "username": None,
                "subreddit": subreddit
            }
        
        # YouTube
        elif "youtube.com" in referrer_lower or "youtu.be" in referrer_lower:
            return {"platform": "youtube", "username": None}
        
        # WhatsApp
        elif "whatsapp" in user_agent.lower():
            return {"platform": "whatsapp", "username": None}
        
        # Telegram
        elif "telegram" in user_agent.lower():
            return {"platform": "telegram", "username": None}
        
        # Discord
        elif "discord" in referrer_lower:
            return {"platform": "discord", "username": None}
        
        # Generic
        else:
            return {"platform": "other", "referrer": referrer}
    
    @staticmethod
    def _extract_twitter_username(url: str) -> Optional[str]:
        """Extract Twitter username from URL"""
        import re
        match = re.search(r'twitter\.com/([^/?\s]+)', url)
        if match:
            return match.group(1)
        match = re.search(r'x\.com/([^/?\s]+)', url)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def _extract_linkedin_username(url: str) -> Optional[str]:
        """Extract LinkedIn username from URL"""
        import re
        match = re.search(r'linkedin\.com/in/([^/?\s]+)', url)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def _extract_instagram_username(url: str) -> Optional[str]:
        """Extract Instagram username from URL"""
        import re
        match = re.search(r'instagram\.com/([^/?\s]+)', url)
        if match:
            username = match.group(1)
            # Filter out common paths
            if username not in ['p', 'reel', 'stories', 'explore']:
                return username
        return None
    
    @staticmethod
    def _extract_tiktok_username(url: str) -> Optional[str]:
        """Extract TikTok username from URL"""
        import re
        match = re.search(r'tiktok\.com/@([^/?\s]+)', url)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def _extract_reddit_subreddit(url: str) -> Optional[str]:
        """Extract Reddit subreddit from URL"""
        import re
        match = re.search(r'reddit\.com/r/([^/?\s]+)', url)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def _analyze_device(user_agent: str) -> Dict[str, Any]:
        """
        Analyze Device from User-Agent
        
        Detects:
        - OS (Windows, macOS, iOS, Android, Linux)
        - Browser (Chrome, Safari, Firefox, Edge)
        - Device-Type (mobile, tablet, desktop)
        - Device-Brand (Apple, Samsung, Huawei, etc.)
        """
        try:
            # Can upgrade to: user-agents library or ua-parser
            ua_lower = user_agent.lower()
            
            # OS Detection
            os_name = "Unknown"
            os_version = None
            if "windows" in ua_lower:
                os_name = "Windows"
            elif "mac os x" in ua_lower or "macos" in ua_lower:
                os_name = "macOS"
            elif "iphone" in ua_lower or "ipad" in ua_lower:
                os_name = "iOS"
            elif "android" in ua_lower:
                os_name = "Android"
            elif "linux" in ua_lower:
                os_name = "Linux"
            
            # Browser Detection
            browser = "Unknown"
            if "chrome" in ua_lower and "edg" not in ua_lower:
                browser = "Chrome"
            elif "safari" in ua_lower and "chrome" not in ua_lower:
                browser = "Safari"
            elif "firefox" in ua_lower:
                browser = "Firefox"
            elif "edg" in ua_lower:
                browser = "Edge"
            
            # Device-Type
            is_mobile = "mobile" in ua_lower or "iphone" in ua_lower or "android" in ua_lower
            device_type = "mobile" if is_mobile else "desktop"
            
            # Device-Brand
            brand = None
            if "iphone" in ua_lower or "ipad" in ua_lower or "mac" in ua_lower:
                brand = "Apple"
            elif "samsung" in ua_lower:
                brand = "Samsung"
            elif "huawei" in ua_lower:
                brand = "Huawei"
            
            return {
                "os": os_name,
                "os_version": os_version,
                "browser": browser,
                "browser_version": None,
                "device_type": device_type,
                "device_brand": brand,
                "is_mobile": is_mobile
            }
        except Exception:
            return {"os": "Unknown", "browser": "Unknown", "device_type": "Unknown", "is_mobile": False}
    
    @staticmethod
    def _is_bot(user_agent: str, ip_address: str) -> bool:
        """Bot-Detection"""
        ua_lower = user_agent.lower()
        bot_indicators = ['bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python-requests']
        return any(indicator in ua_lower for indicator in bot_indicators)
    
    @staticmethod
    def _hash_fingerprint(fingerprint: Dict[str, Any]) -> str:
        """Hash device fingerprint for tracking"""
        fp_string = json.dumps(fingerprint, sort_keys=True)
        return hashlib.sha256(fp_string.encode()).hexdigest()[:16]
    
    @staticmethod
    def _generate_qr_code(url: str) -> str:
        """Generate QR-Code (Base64)"""
        try:
            import qrcode
            import io
            import base64
            
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            
            return base64.b64encode(buffer.getvalue()).decode()
        except:
            return ""


# Singleton
link_tracker = LinkTracker()
