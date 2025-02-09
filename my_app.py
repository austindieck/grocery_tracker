import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from supabase import create_client, Client
import os

# 🟢 Supabase API Config (Read from Environment Variables)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # Required for Render Deployment

all_data = []
limit = 1000  # Supabase row limit per request
offset = 0

while True:
    response = (
        supabase.table("grocery_prices")
        .select("*")
        .order("scrape_date", desc=True)  # Fetch newest records first
        .range(offset, offset + limit - 1)  # Get 1000 rows at a time
        .execute()
    )

    data_chunk = response.data

    if not data_chunk:  # Stop when no more data is returned
        break

    all_data.extend(data_chunk)  # Add fetched data
    offset += limit  # Move to the next batch

# Convert to DataFrame
df = pd.DataFrame(all_data) if all_data else pd.DataFrame()

# Debug: Print total rows retrieved
print(f"\nTotal Rows Fetched from Supabase (After Pagination): {len(df)}")

# Ensure scrape_date is in datetime format
if "scrape_date" in df.columns:
    df["scrape_date"] = pd.to_datetime(df["scrape_date"], errors="coerce")

# Sort data **ascending** to ensure proper plotting
df = df.sort_values(by="scrape_date", ascending=True)

# Debugging: Check full date range
print("\nEarliest Date in Data:", df["scrape_date"].min())
print("Latest Date in Data:", df["scrape_date"].max())

# Get unique product names for dropdown
product_options = [{"label": p, "value": p} for p in df["product_name"].unique()] if not df.empty else []

# 🖌️ Layout with Two-Column Structure
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "margin": "20px auto",
        "maxWidth": "1400px",
        "display": "flex",
        "gap": "20px",
        "backgroundColor": "#F0E2D3",
        "borderRadius": "10px",
        "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.1)",
        "padding": "40px",
    },
    children=[
        # Left Column (Main Content)
        html.Div(
            style={"flex": "3"},
            children=[
                # Banner
                html.Div(
                    style={
                        "backgroundColor": "#A2A9A3",
                        "color": "white",
                        "textAlign": "center",
                        "padding": "15px",
                        "borderRadius": "10px",
                        "fontSize": "24px",
                        "fontWeight": "bold",
                    },
                    children="Grocery Price Tracker",
                ),

                # Dropdown for selecting products
                html.Div(
                    style={"marginTop": "20px"},
                    children=[
                        html.Label("Select Products:", style={"fontSize": "18px", "fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="product-dropdown",
                            options=product_options,
                            multi=True,
                            placeholder="Choose one or more products...",
                            style={"width": "100%", "padding": "5px"},
                        ),
                    ],
                ),

                # Graph to display price trends
                dcc.Graph(id="price-trend-plot"),
            ],
        ),

        # Right Column (Price Alerts)
        html.Div(
            style={
                "flex": "1",
                "display": "flex",
                "flexDirection": "column",
                "gap": "10px",
                "alignItems": "center",
                "borderLeft": "2px solid #ccc",
                "paddingLeft": "10px",
                "minWidth": "250px",
            },
            children=[
                html.H4("Price Alerts", style={"marginBottom": "10px"}),
                html.Div(id="price-alerts"),
            ],
        ),
    ],
)

@app.callback(
    Output("price-alerts", "children"),
    Input("product-dropdown", "id")  # This runs once when the page loads
)
def update_price_alerts(_):
    if df.empty:
        return [html.Div("No data available.", style={"textAlign": "center", "padding": "10px"})]

    # Get the most recent two days in the dataset
    latest_dates = df["scrape_date"].drop_duplicates().nlargest(2).tolist()
    if len(latest_dates) < 2:
        return [html.Div("Not enough data for price changes.", style={"textAlign": "center", "padding": "10px"})]

    today, yesterday = latest_dates  # Extract the two most recent days

    # 🟢 **Step 1: Filter dataset to only include the last two days**
    df_recent = df[df["scrape_date"].isin([today, yesterday])]

    # 🟢 **Step 2: Aggregate prices by taking the average per product per day**
    df_avg = df_recent.groupby(["product_name", "scrape_date"])["price"].mean().reset_index()

    # 🟢 **Step 3: Pivot the data so that each product has prices for the last two days**
    df_pivot = df_avg.pivot(index="product_name", columns="scrape_date", values="price").dropna()

    # Rename columns for clarity
    df_pivot.columns = ["yesterday_price", "today_price"]

    # 🟢 **Step 4: Calculate percentage price change**
    df_pivot["price_change"] = ((df_pivot["today_price"] - df_pivot["yesterday_price"]) / df_pivot["yesterday_price"]) * 100

    # 🟢 **Step 5: Get the top 10 most significant price changes**
    top_changes = df_pivot["price_change"].abs().nlargest(10)

    # **Step 6: Format results for display**
    alerts = [
        {
            "product": product,
            "change": df_pivot.loc[product, "price_change"],
            "color": "red" if df_pivot.loc[product, "price_change"] > 0 else "green"
        }
        for product in top_changes.index
    ]

    # **Step 7: Return alerts**
    if not alerts:
        return [html.Div("No significant price changes.", style={"textAlign": "center", "padding": "10px"})]

    return [
        html.Div(
            f"{alert['product']}: {'↑' if alert['color'] == 'red' else '↓'} {alert['change']:.2f}%",
            style={
                "padding": "10px",
                "margin": "10px",
                "borderRadius": "5px",
                "color": "white",
                "backgroundColor": alert["color"],
                "fontWeight": "bold",
                "width": "100%",
                "textAlign": "center",
            },
        )
        for alert in alerts
    ]

# 🟢 Callback to Update the Plot Based on Selected Products
@app.callback(
    Output("price-trend-plot", "figure"),
    Input("product-dropdown", "value")
)
def update_plot(selected_products):
    print("Selected Products:", selected_products)  # Debugging statement

    if df.empty or not selected_products:
        return px.line(title="Select products to see trends")

    # Filter for selected products
    filtered_df = df[df["product_name"].isin(selected_products)]

    # Create line plot instead of scatter for trend visualization
    fig = px.line(
        filtered_df,
        x="scrape_date",
        y="price",
        color="product_name",
        title="Grocery Price Trends Over Time",
        labels={"price": "Price ($)", "scrape_date": "Date"},
        template="plotly_white",
    )

    return fig

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)