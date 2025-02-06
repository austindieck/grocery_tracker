import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from supabase import create_client, Client
import os

# 🟢 Supabase API Config (Read from Environment Variables)
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qbccysstzmoklbagcqzl.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-service-role-key")  # Replace with your actual key

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Dash app
app = dash.Dash(__name__)

# 🟢 Fetch data from Supabase when the app loads
response = supabase.table("grocery_prices").select("*").execute()
df = pd.DataFrame(response.data) if response.data else pd.DataFrame()

# Get unique product names for dropdown
product_options = [{"label": p, "value": p} for p in df["product_name"].unique()] if not df.empty else []

# 🖌️ Minimalist UI with a banner and better layout
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "margin": "20px auto",
        "maxWidth": "900px",
        "padding": "20px",
        "backgroundColor": "#F0E2D3",
        "borderRadius": "10px",
        "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.1)",
    },
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
                    placeholder="",
                    style={"width": "100%", "padding": "5px"},
                ),
            ],
        ),

        # Graph to display price trends
        dcc.Graph(id="price-trend-plot"),

        # Author Signature
        html.Div(
            "Author: Austin Dieck",
            style={
                "position": "absolute",
                "bottom": "10px",
                "right": "20px",
                "color": "#666",
                "fontSize": "14px",
            },
        ),
    ],
)

# 🟢 Callback to Update the Plot Based on Selected Products
@app.callback(
    Output("price-trend-plot", "figure"),
    Input("product-dropdown", "value")
)
def update_plot(selected_products):
    if not selected_products or df.empty:
        return px.scatter(title="Select products to see trends")

    # Convert `scrape_date` to datetime
    df["scrape_date"] = pd.to_datetime(df["scrape_date"])

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