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

# 🟢 Fetch data from Supabase when the app loads
response = supabase.table("grocery_prices").select("*").execute()
df = pd.DataFrame(response.data) if response.data else pd.DataFrame()

# Convert scrape_date to datetime
df["scrape_date"] = pd.to_datetime(df["scrape_date"])

# Get unique product names for dropdown
product_options = [{"label": p, "value": p} for p in df["product_name"].unique()] if not df.empty else []

# 🟢 Calculate Top 10 Price Changes
def get_price_changes():
    if df.empty:
        return []

    # Get the most recent two days in the dataset
    latest_dates = df["scrape_date"].drop_duplicates().nlargest(2).tolist()
    if len(latest_dates) < 2:
        return []

    today, yesterday = latest_dates

    # Filter for the last two days
    today_prices = df[df["scrape_date"] == today].set_index("product_name")["price"]
    yesterday_prices = df[df["scrape_date"] == yesterday].set_index("product_name")["price"]

    # Calculate percentage change
    price_changes = ((today_prices - yesterday_prices) / yesterday_prices * 100).dropna()
    
    # Sort by absolute change and get top 10
    top_changes = price_changes.abs().nlargest(10)

    # Format results for display
    alerts = [
        {
            "product": product,
            "change": price_changes[product],
            "color": "red" if price_changes[product] > 0 else "green"
        }
        for product in top_changes.index
    ]
    
    return alerts

# 🖌️ Layout with Two-Column Structure
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "margin": "20px auto",
        "maxWidth": "1400px",
        "display": "flex",  # Uses flexbox for column layout
        "gap": "20px",
        "backgroundColor": "#F0E2D3",
        "borderRadius": "10px",
        "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.1)",
        "padding": "40px",
    },
    children=[
        # Left Column (Main Content)
        html.Div(
            style={"flex": "3"},  # Takes 3x space compared to alerts column
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
                "flex": "1",  # Takes less space than the main column
                "display": "flex",
                "flexDirection": "column",
                "gap": "10px",
                "alignItems": "center",
                "borderLeft": "2px solid #ccc",
                "paddingLeft": "10px",
                "minWidth": "250px",  # Ensures alerts fit well
            },
            children=[
                html.H4("Price Alerts", style={"marginBottom": "10px"}),  # Title
                html.Div(id="price-alerts"),  # Alerts container
            ],
        ),
    ],
)

# 🟢 Callback to Generate Price Alerts
@app.callback(
    Output("price-alerts", "children"),
    Input("product-dropdown", "id")  # Triggers once when page loads
)
def update_price_alerts(_):
    alerts = get_price_changes()
    
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
                "width": "100%",  # Makes sure alerts are the same width
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
    if not selected_products or df.empty:
        return px.scatter(title="Select products to see trends")

    # Filter for selected products
    filtered_df = df[df["product_name"].isin(selected_products)]

    # Create scatter plot
    fig = px.scatter(
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
