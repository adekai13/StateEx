import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

google_service_account_info = st.secrets['google_service_account']
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_service_account_info, scopes=scope)

# Function to read data from Google Sheets
@st.cache_data(ttl=30)
def read_google_sheet(_credentials):
    try:
        client = gspread.authorize(_credentials)
        sheet = client.open('adil')
        worksheet = sheet.get_worksheet(0)
        data = worksheet.get_all_values()

        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df
        else:
            st.write("No data available in the Google Sheet.")
            return None
    except Exception as e:
        st.write(f"An error occurred: {str(e)}")
        return None

# Function to calculate profit and return the DataFrame
def calculate_profit(selected_countries, selected_salespersons, df):
    if df is not None:
        try:
            # Filter data based on selected countries and/or salespersons
            filtered_data = df.loc[
                (df["ShipCountry"].isin(selected_countries) if selected_countries else df["ShipCountry"]) &
                (df["SalesPerson"].isin(selected_salespersons) if selected_salespersons else df["SalesPerson"])
            ].copy()  # Make a copy after filtering to avoid SettingWithCopyWarning

            # Convert columns to numeric data types using .loc to avoid SettingWithCopyWarning
            for col in ['Units_Sold', 'Unit_Sales_Price', 'Unit_Cost']:
                filtered_data.loc[:, col] = pd.to_numeric(filtered_data[col], errors='coerce')

            # Calculate profit
            filtered_data.loc[:, "Profit"] = filtered_data["Units_Sold"] * (filtered_data["Unit_Sales_Price"] - filtered_data["Unit_Cost"])

            return filtered_data
        except Exception as e:
            st.write(f"An error occurred during profit calculation: {str(e)}")
            return None
    else:
        return None

# Function to plot dynamic graphs
def plot_dynamic_graph(df, x_variable, graph_type):
    st.subheader(f"Dynamic Graph for {x_variable}")
    fig, ax = plt.subplots()

    if graph_type == "Histogram":
        sns.histplot(data=df, x=x_variable, kde=True, ax=ax)
    elif graph_type == "Pie Chart":
        df = df[x_variable].value_counts()
        plt.pie(df, labels=df.index, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    st.pyplot(fig)

# Streamlit app
st.title("Dynamic Graphs and Profit Calculation")

# Read data from Google Sheets
df = read_google_sheet(credentials)

# Store the last fetched data
last_data = df.copy() if df is not None else None

if df is not None:
    # Get unique values for countries and salespersons
    countries = df["ShipCountry"].unique().tolist()
    salespersons = df["SalesPerson"].unique().tolist()

    # Dropdown for selecting multiple countries and/or salespersons
    selected_countries = st.multiselect("Select Ship Countries", countries, default=countries)
    selected_salespersons = st.multiselect("Select Salespersons", salespersons, default=salespersons)

    # Dropdown for selecting the graph type
    graph_types = ["Histogram", "Pie Chart"]
    selected_graph_type = st.selectbox("Select Graph Type", graph_types)

    # Define variables for each graph type
    histogram_variables = ["Units_Sold", "Unit_Sales_Price", "Unit_Cost", "Profit"]
    pie_chart_variables = ["SalesPerson", "ShipCountry", "CompanyName"]

    # Conditional dropdown for selecting the variable to plot
    if selected_graph_type == "Histogram":
        selected_variable = st.selectbox("Select Variable to Plot", histogram_variables)
    elif selected_graph_type == "Pie Chart":
        selected_variable = st.selectbox("Select Variable to Plot", pie_chart_variables)

    # Call the function to filter data based on user selection
    filtered_data = calculate_profit(selected_countries, selected_salespersons, df)

    # Show filtered data and dynamic graphs
    if filtered_data is not None and len(filtered_data) > 0:
        st.write("Filtered Data:")
        st.write(filtered_data)

        # Plot dynamic graph based on selected type
        plot_dynamic_graph(filtered_data, selected_variable, selected_graph_type)
    else:
        st.write("No data available for selected country and salesperson combination.")

# Check if data has changed and trigger rerun if necessary
if df is not None and last_data is not None:
    if not df.equals(last_data):
        st.rerun()
