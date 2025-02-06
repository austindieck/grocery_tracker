import tkinter as tk
import customtkinter as ctk
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Database Configuration
DB_CONFIG = {
    "dbname": "grocery_prices",
    "user": "austindieck",
    "password": "",  # Add password if needed
    "host": "localhost",
    "port": "5432"
}

# Function to fetch unique product names
def get_product_names():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        query = "SELECT DISTINCT product_name FROM grocery_prices ORDER BY product_name;"
        df = pd.read_sql(query, conn)
        conn.close()
        return df["product_name"].tolist()
    except Exception as e:
        print("Database error:", e)
        return []

# Function to fetch price data for a selected product
def get_price_data(product_name):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        query = """
            SELECT scrape_date, price 
            FROM grocery_prices 
            WHERE product_name = %s 
            ORDER BY scrape_date;
        """
        df = pd.read_sql(query, conn, params=(product_name,))
        conn.close()
        return df
    except Exception as e:
        print("Database error:", e)
        return pd.DataFrame()

# Function to update the plot
def update_plot():
    selected_product = product_dropdown.get()
    if not selected_product:
        return
    
    df = get_price_data(selected_product)
    
    if df.empty:
        print("No data available for", selected_product)
        return
    
    ax.clear()
    ax.plot(df["scrape_date"], df["price"], marker='o', linestyle='-', color='blue')
    ax.set_title(f"Price Trend: {selected_product}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    ax.grid(True)
    plt.xticks(rotation=90)
    fig.subplots_adjust(left=0.15, right=0.95, top=0.90, bottom=0.25)  # Adjust padding
    canvas.draw()

# Initialize Tkinter App
ctk.set_appearance_mode("System")  # Light/Dark Mode
root = ctk.CTk()
root.title("Grocery Price Tracker")
root.geometry("600x500")

# Dropdown Menu
tk.Label(root, text="Select a Product:").pack(pady=10)
product_names = get_product_names()
product_dropdown = ctk.CTkComboBox(root, values=product_names, command=lambda _: update_plot())
product_dropdown.pack()

# Matplotlib Figure
fig, ax = plt.subplots()
fig.subplots_adjust(left=0.15, right=0.95, top=0.90, bottom=0.25)  # Adjust padding
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Run Tkinter App
root.mainloop()
