from supabase import create_client, Client
import psycopg2
import json  # To format API responses

# 🟢 Local PostgreSQL Database Config
LOCAL_DB_CONFIG = {
    "host": "localhost",
    "database": "grocery_prices",
    "user": "austindieck",
    # "password": "your_local_password"  # Uncomment if needed
}

# 🟢 Supabase API Config
SUPABASE_URL = "https://qbccysstzmoklbagcqzl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFiY2N5c3N0em1va2xiYWdjcXpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczODgwNzAxNywiZXhwIjoyMDU0MzgzMDE3fQ.cCFj4M3hzmhUHVtvxrCPdro-DR1rcDLPJZ3BM2gjxlU"  # Replace with actual service role key

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    print("🔄 Connecting to local database...")
    local_conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    local_cur = local_conn.cursor()

    # 3️⃣ Fetch Data from Local DB
    local_cur.execute("SELECT id, store_name, product_name, price, scrape_date FROM grocery_prices;")
    rows = local_cur.fetchall()
    print(f"🔄 Fetched {len(rows)} rows from local database.")

    # 4️⃣ Insert Data into Supabase via REST API
    for row in rows:
        data = {
            "id": row[0],
            "store_name": row[1],
            "product_name": row[2],
            "price": float(row[3]),  # ✅ Convert Decimal to float
            "scrape_date": row[4].isoformat(),  # ✅ Convert date to string
        }
        
        # Send data to Supabase and capture response
        response = supabase.table("grocery_prices").upsert([data]).execute()

        # 🔍 Debugging: Print Full Response
        print(f"🔍 Sent Data: {json.dumps(data, indent=2)}")  # Pretty-print sent data
        print(f"🔍 Supabase Response Status: {response.status_code if hasattr(response, 'status_code') else 'No Status Code'}")

        # Print API response (either error or success data)
        if hasattr(response, 'data') and response.data:
            print(f"✅ Supabase Response Data: {json.dumps(response.data, indent=2)}")
        elif hasattr(response, 'error') and response.error:
            print(f"❌ Supabase API Error: {json.dumps(response.error, indent=2)}")
        else:
            print(f"⚠️ Unexpected API Response: {response}")

    print("✅ Data successfully migrated to Supabase!")

except Exception as e:
    print("❌ Python Error:", e)

finally:
    # Close local DB connection
    if 'local_cur' in locals():
        local_cur.close()
    if 'local_conn' in locals():
        local_conn.close()
    print("✅ Local database connection closed.")