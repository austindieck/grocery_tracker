import requests
from bs4 import BeautifulSoup
import time
import random
import os
from fake_useragent import UserAgent
from datetime import datetime
from supabase import create_client, Client

# 🟢 Supabase API Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Generate a random User-Agent
ua = UserAgent()

# Function to insert/update prices in Supabase
def save_to_supabase(store_name, product_name, price):
    try:
        # Convert price to a decimal value
        price = float(price.replace("$", "").replace(",", "").strip())

        # Data to insert into Supabase
        data = {
            "store_name": store_name,
            "product_name": product_name,
            "price": price,
            "scrape_date": datetime.today().strftime('%Y-%m-%d')  # Format YYYY-MM-DD
        }

        # Insert or update using upsert
        response = supabase.table("grocery_prices").upsert([data]).execute()

        # Debugging: Print Supabase response
        if response.data:
            print(f"✅ Inserted: {data} → {response.data}")
        elif response.error:
            print(f"❌ Supabase API Error: {response.error}")

    except Exception as e:
        print("❌ Error saving to Supabase:", e)

# Function to scrape a single Aldi page
def scrape_aldi_page(url, store_name):
    headers = {"User-Agent": ua.random}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch {url} (status code: {response.status_code})")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    products = []

    product_tiles = soup.find_all('div', class_='product-tile')
    for tile in product_tiles:
        name = tile.find('div', class_='product-tile__name')
        name = name.p.text.strip() if name else "N/A"

        price_container = tile.find('span', class_='base-price__regular')
        price = price_container.find('span').text.strip() if price_container else "N/A"

        unit = tile.find('div', class_='product-tile__unit-of-measurement')
        unit = unit.p.text.strip() if unit else "N/A"

        if price != "N/A":
            save_to_supabase(store_name, name, price)

        products.append({"name": name, "price": price, "unit": unit})

    return products

# Function to scrape multiple Aldi pages
def scrape_aldi_pages(base_url, start_page, end_page, store_name):
    pages = list(range(start_page, end_page + 1))
    random.shuffle(pages)

    for page in pages:
        url = f"{base_url}?page={page}"
        print(f"Scraping: {url}")

        scrape_aldi_page(url, store_name)

        delay = random.uniform(1, 5)
        print(f"Waiting for {delay:.2f} seconds...")
        time.sleep(delay)

# Run the scraper for different Aldi categories
categories = {
    "Meat & Seafood": "https://new.aldi.us/products/fresh-meat-seafood/k/12",
    "Produce": "https://new.aldi.us/products/fresh-produce/k/13",
    "Dairy & Eggs": "https://new.aldi.us/products/dairy-eggs/k/10",
    "Deli": "https://new.aldi.us/products/deli/k/11"
}

for category, url in categories.items():
    scrape_aldi_pages(url, start_page=1, end_page=5, store_name="Aldi")

print("✅ Scraping completed and saved to Supabase.")
