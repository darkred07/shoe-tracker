#!/usr/bin/env python3
"""
Shoe Price Tracker using Google Gemini API
Tracks shoe prices from multiple URLs and alerts when prices drop below thresholds.
"""

import json
import os
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please add it to your .env file")

genai.configure(api_key=GEMINI_API_KEY)

# Email Configuration (optional)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO', '').split(',') if os.getenv('EMAIL_TO') else []

# Configuration
TRACKED_URLS_FILE = 'tracked_urls.json'
PRICE_HISTORY_FILE = 'price_history.json'


class ShoeTracker:
    def __init__(self):
        config = self.load_config()
        self.settings = config.get('settings', {})
        self.tracked_urls = config.get('urls', [])
        self.price_history = self.load_price_history()
        
        # Initialize model from settings
        model_name = self.settings.get('model', 'gemini-2.5-pro')
        self.model = genai.GenerativeModel(model_name)
        print(f"🤖 Using model: {model_name}")
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file."""
        if not os.path.exists(TRACKED_URLS_FILE):
            print(f"⚠️  {TRACKED_URLS_FILE} not found. Creating empty file...")
            default_config = {
                "settings": {"model": "gemini-2.5-pro", "threshold": 50000},
                "urls": []
            }
            self.save_config(default_config)
            return default_config
        
        try:
            with open(TRACKED_URLS_FILE, 'r') as f:
                config = json.load(f)
                
                # Handle old format (array) - convert to new format
                if isinstance(config, list):
                    print(f"⚠️  Converting old config format to new format...")
                    new_config = {
                        "settings": {"model": "gemini-2.5-pro", "threshold": 50000},
                        "urls": config
                    }
                    self.save_config(new_config)
                    return new_config
                
                return config
        except json.JSONDecodeError:
            print(f"❌ Error reading {TRACKED_URLS_FILE}. Starting with empty config.")
            return {"settings": {"model": "gemini-2.5-pro", "threshold": 50000}, "urls": []}
    
    def save_config(self, config: Dict):
        """Save configuration to JSON file."""
        with open(TRACKED_URLS_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_price_history(self) -> Dict:
        """Load price history from JSON file."""
        if not os.path.exists(PRICE_HISTORY_FILE):
            return {}
        
        try:
            with open(PRICE_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    
    def save_price_history(self):
        """Save price history to JSON file."""
        with open(PRICE_HISTORY_FILE, 'w') as f:
            json.dump(self.price_history, f, indent=2)
    
    
    def send_email(self, alerts: List[Dict]):
        """Send email alert using Amazon SES.
        
        Args:
            alerts: List of alert dictionaries containing product info
        """
        if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, EMAIL_FROM, EMAIL_TO]):
            print("   ⚠️  Email not configured. Skipping email notification.")
            return
        
        try:
            # Create SES client
            ses_client = boto3.client(
                'ses',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
            
            # Build email content
            subject = f"🚨 Shoe Price Alert: {len(alerts)} Product(s) Below Threshold!"
            
            # HTML body
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ background-color: #f44336; color: white; padding: 20px; }}
                    .product {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; }}
                    .price {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
                    .savings {{ color: #ff5722; }}
                    .button {{ background-color: #2196F3; color: white; padding: 10px 20px; 
                              text-decoration: none; display: inline-block; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🚨 Shoe Price Alert!</h1>
                    <p>Found {len(alerts)} product(s) below your threshold</p>
                </div>
                <div style="padding: 20px;">
            """
            
            # Text body (fallback)
            text_body = f"Shoe Price Alert: {len(alerts)} product(s) below threshold!\n\n"
            
            for i, alert in enumerate(alerts, 1):
                savings = alert['threshold'] - alert['price']
                
                html_body += f"""
                <div class="product">
                    <h2>#{i}: {alert['product_name']}</h2>
                    <p><strong>Listing:</strong> {alert['listing_name']}</p>
                    <p class="price">Price: ${alert['price']:,.2f}</p>
                    <p class="savings">💰 Save: ${savings:,.2f} (Threshold: ${alert['threshold']:,.2f})</p>
                    <a href="{alert['url']}" class="button">View Product</a>
                </div>
                """
                
                text_body += f"""
Product #{i}: {alert['product_name']}
Listing: {alert['listing_name']}
Price: ${alert['price']:,.2f}
Save: ${savings:,.2f} (Threshold: ${alert['threshold']:,.2f})
URL: {alert['url']}

"""
            
            html_body += """
                </div>
            </body>
            </html>
            """
            
            # Clean recipient emails
            recipients = [email.strip() for email in EMAIL_TO if email.strip()]
            
            # Send email
            response = ses_client.send_email(
                Source=EMAIL_FROM,
                Destination={'ToAddresses': recipients},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Text': {'Data': text_body},
                        'Html': {'Data': html_body}
                    }
                }
            )
            
            print(f"   ✅ Email sent successfully! Message ID: {response['MessageId']}")
            print(f"   📧 Sent to: {', '.join(recipients)}")
            
        except ClientError as e:
            print(f"   ❌ Error sending email: {e.response['Error']['Message']}")
        except Exception as e:
            print(f"   ❌ Unexpected error sending email: {e}")
    def fetch_page_content(self, url: str, selector: str = None) -> Optional[str]:
        """Fetch product gallery HTML from URL using headless browser.
        
        Args:
            url: URL to fetch
            selector: CSS selector for product container (e.g., '#gallery-layout-container')
                     If None, returns entire body HTML
        """
        from playwright.sync_api import sync_playwright
        
        try:
            print(f"   🌐 Loading page with JavaScript rendering...")
            
            with sync_playwright() as p:
                # Launch headless browser
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                
                # Navigate with more lenient wait condition
                page.goto(url, wait_until='load', timeout=60000)
                
                # If selector provided, wait for it
                if selector:
                    try:
                        page.wait_for_selector(selector, timeout=10000)
                        print(f"   ✅ Selector '{selector}' found")
                    except:
                        print(f"   ⚠️  Selector '{selector}' not found, using fallback...")
                else:
                    page.wait_for_timeout(5000)
                
                # Scroll to load lazy content
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)
                
                # Extract HTML from selector or entire body
                if selector:
                    gallery_html = page.evaluate(f"""
                        () => {{
                            const element = document.querySelector('{selector}');
                            return element ? element.innerHTML : document.body.innerHTML;
                        }}
                    """)
                else:
                    gallery_html = page.evaluate("() => document.body.innerHTML")
                
                browser.close()
                
                print(f"   ✅ Content extracted ({len(gallery_html):,} characters)")
                return gallery_html
                
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            return None
    
    def extract_products_with_gemini(self, html_content: str, url: str, threshold: float, debug: bool = True) -> tuple[List[Dict], List[Dict]]:
        """Use Gemini API to extract all products from a listing page.
        Returns: (products_below_threshold, all_products)
        """
        # Send gallery HTML to Gemini (already focused on products)
        print(f"   🤖 Analyzing {len(html_content):,} chars of product gallery with Gemini AI...")
        
        prompt = f"""
You are analyzing HTML from a product gallery container (id="gallery-layout-container") from an e-commerce site.
Extract ALL shoes/products visible in this gallery.

URL: {url}

IMPORTANT: Argentine peso prices often have periods as thousands separators.
For example: "99.999" means 99,999 pesos (not 99.99).

Product Gallery HTML:
{html_content}

Instructions:
1. Find ALL products/shoes listed on this page
2. For EACH product, extract:
   - Product name/title (look for product titles, h2, h3, span with product names)
   - Current selling price in numbers only
   - Product URL if available (look for product links)
3. Price handling:
   - Remove ALL currency symbols ($, AR$, etc)
   - Remove ALL non-numeric characters except periods and commas
   - If price uses period as thousands separator (e.g., "99.999"), keep it as 99999
   - If price uses comma as decimal (e.g., "99,99"), convert to 99.99
4. Return data as JSON array
5. ONLY include products that have visible prices

Return ONLY valid JSON in this exact format (no markdown, no code blocks, no extra text):
[
  {{"name": "Product Name", "price": 99999, "url": "product-url-or-empty-string"}},
  {{"name": "Another Product", "price": 149999, "url": "product-url-or-empty-string"}}
]

If no products found, return: []
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parse JSON
            products = json.loads(response_text)
            
            if not isinstance(products, list):
                print(f"   ⚠️  Unexpected response format")
                if debug:
                    print(f"   📋 Raw response: {response_text[:300]}...")
                return [], []
            
            # Debug: Show all products found
            if debug and products:
                print(f"\n   📦 Total products extracted: {len(products)}")
                print(f"   💵 Price range: ${min(p.get('price', 0) for p in products):,.2f} - ${max(p.get('price', 0) for p in products):,.2f}")
                print(f"\n   📋 All products found:")
                for i, product in enumerate(products[:10], 1):  # Show first 10
                    print(f"      {i}. {product.get('name', 'Unknown')}: ${product.get('price', 0):,.2f}")
                if len(products) > 10:
                    print(f"      ... and {len(products) - 10} more")
            
            # Filter by threshold and shoe names
            shoe_names = self.settings.get('shoe_names', [])
            below_threshold = []
            
            for product in products:
                # First check if price is below threshold
                if 'price' in product and product['price'] <= threshold:
                    # If shoe_names filter is empty, include all products
                    if not shoe_names:
                        below_threshold.append(product)
                    else:
                        # Check if product name contains any of the shoe names (case-insensitive)
                        product_name = product.get('name', '').lower()
                        if any(shoe_name.lower() in product_name for shoe_name in shoe_names):
                            below_threshold.append(product)
            
            return below_threshold, products
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"   📋 Raw response: {response_text[:500]}...")
            return [], []
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return [], []
    
    def check_listing(self, item: Dict) -> List[Dict]:
        """Check a listing page for all products below threshold."""
        url = item['url']
        listing_name = item['name']
        # Use URL-specific threshold if provided, otherwise use default from settings
        threshold = item.get('threshold', self.settings.get('threshold', 50000))
        selector = item.get('selector')  # Optional selector
        
        print(f"\n🔍 Checking listing: {listing_name}")
        print(f"   URL: {url}")
        if selector:
            print(f"   🎯 Using selector: {selector}")
        print(f"   💰 Threshold: ${threshold:,.2f}")
        
        # Show active name filters
        shoe_names = self.settings.get('shoe_names', [])
        if shoe_names:
            print(f"   👟 Name filters: {', '.join(shoe_names)}")
        
        # Fetch page content with optional selector
        html_content = self.fetch_page_content(url, selector)
        if not html_content:
            return []
        
        # Extract all products below threshold using Gemini
        products_below_threshold, all_products = self.extract_products_with_gemini(html_content, url, threshold, debug=True)
        
        if not products_below_threshold:
            if all_products:
                print(f"   ✅ Found {len(all_products)} products, but none below threshold")
            else:
                print(f"   ⚠️  No products extracted from page")
            return []
        
        print(f"\n   🚨 Found {len(products_below_threshold)} product(s) below threshold!")
        
        results = []
        for product in products_below_threshold:
            product_name = product.get('name', 'Unknown Product')
            price = product.get('price', 0)
            product_url = product.get('url', '')
            
            # Convert relative URLs to absolute URLs
            if product_url and not product_url.startswith('http'):
                from urllib.parse import urljoin
                product_url = urljoin(url, product_url)
            elif not product_url:
                # If no URL provided, use the listing URL
                product_url = url
            
            print(f"\n   💰 {product_name}")
            print(f"      Price: ${price:,.2f} (threshold: ${threshold:,.2f})")
            print(f"      🛒 {product_url}")
            
            result = {
                'listing_name': listing_name,
                'product_name': product_name,
                'url': product_url,
                'price': price,
                'threshold': threshold,
                'timestamp': datetime.now().isoformat(),
                'alert': True
            }
            
            results.append(result)
            
            # Update price history
            if product_url not in self.price_history:
                self.price_history[product_url] = []
            
            self.price_history[product_url].append({
                'price': price,
                'timestamp': result['timestamp']
            })
            
            # Keep last 30 entries
            self.price_history[product_url] = self.price_history[product_url][-30:]
        
        return results
    
    def run_check(self):
        """Run price check for all tracked URLs."""
        if not self.tracked_urls:
            print("⚠️  No URLs tracked. Add URLs to tracked_urls.json")
            return
        
        print("=" * 70)
        print(f"🏃 Starting price check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        all_alerts = []
        
        for i, item in enumerate(self.tracked_urls):
            results = self.check_listing(item)
            all_alerts.extend(results)
            
            # Rate limiting: max 2 URLs per minute (30 second delay between checks)
            # Skip delay after the last URL
            if i < len(self.tracked_urls) - 1:
                print(f"\n⏳ Rate limiting: waiting 30 seconds before next check...")
                time.sleep(30)
        
        # Save price history
        self.save_price_history()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"✅ Checked: {len(self.tracked_urls)} listing(s)")
        
        if all_alerts:
            print(f"\n🚨 {len(all_alerts)} SHOE(S) BELOW THRESHOLD!")
            print("=" * 70)
            
            for alert in all_alerts:
                print(f"\n🔥 {alert['product_name']}")
                print(f"   💰 Price: ${alert['price']:,.2f} (Save: ${alert['threshold'] - alert['price']:,.2f})")
                print(f"   🛒 {alert['url']}")
            
            # Send email notification
            print("\n" + "=" * 70)
            print("📧 SENDING EMAIL NOTIFICATION")
            print("=" * 70)
            self.send_email(all_alerts)
        else:
            print(f"\n😴 No shoes below threshold found")
        
        print("\n" + "=" * 70)


def main():
    """Main entry point."""
    tracker = ShoeTracker()
    tracker.run_check()


if __name__ == '__main__':
    main()
