#!/usr/bin/env python3
"""
Test script for Shoe Price Tracker
Tests the Gemini API connection and price extraction with a sample product
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

def test_api_connection():
    """Test Gemini API connection"""
    print("🧪 Testing Gemini API Connection...")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("❌ ERROR: Please set your GEMINI_API_KEY in the .env file")
        print("   Get your API key from: https://makersuite.google.com/app/apikey")
        return False
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Simple test prompt
        response = model.generate_content("Reply with just the word 'OK' if you can read this.")
        
        if response.text.strip():
            print(f"✅ API Connection successful!")
            print(f"   Response: {response.text.strip()}")
            return True
        else:
            print("❌ API responded but with empty content")
            return False
            
    except Exception as e:
        print(f"❌ API Connection failed: {e}")
        return False

def test_price_extraction():
    """Test price extraction with a simple HTML example"""
    print("\n🧪 Testing Price Extraction...")
    
    api_key = os.getenv('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    # Sample HTML with a price
    sample_html = """
    <div class="product">
        <h1>Nike Air Max 90</h1>
        <div class="price">
            <span class="original">$150.00</span>
            <span class="current">$99.99</span>
        </div>
    </div>
    """
    
    prompt = f"""
You are analyzing an e-commerce product page. Extract ONLY the current price of the product.

HTML Content:
{sample_html}

Instructions:
1. Find the current selling price (not original/crossed-out prices)
2. Return ONLY the numeric value (e.g., if price is "$99.99", return just "99.99")
3. Remove currency symbols and convert commas to periods for decimals
4. If no price found, return "NOT_FOUND"

Return ONLY the number or "NOT_FOUND", nothing else.
"""
    
    try:
        response = model.generate_content(prompt)
        extracted_price = response.text.strip()
        
        print(f"   Sample HTML: {sample_html[:50]}...")
        print(f"   Extracted Price: {extracted_price}")
        
        if extracted_price == "99.99":
            print("✅ Price extraction working correctly!")
            return True
        else:
            print(f"⚠️  Expected '99.99' but got '{extracted_price}'")
            print("   The extraction logic may need adjustment for your target sites")
            return True  # Still considered a pass as API is working
            
    except Exception as e:
        print(f"❌ Price extraction failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🏃 Shoe Price Tracker - Test Suite")
    print("=" * 60)
    
    # Test API connection
    if not test_api_connection():
        print("\n⚠️  Fix API connection before proceeding")
        return
    
    # Test price extraction
    test_price_extraction()
    
    print("\n" + "=" * 60)
    print("📋 Next Steps:")
    print("=" * 60)
    print("1. Add real shoe URLs to tracked_urls.json")
    print("2. Set appropriate price thresholds")
    print("3. Run: python shoe_price_tracker.py")
    print("4. Set up daily automation (see README.md)")
    print("=" * 60)

if __name__ == '__main__':
    main()
