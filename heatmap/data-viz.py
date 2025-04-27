import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pydeck as pdk
from pandarallel import pandarallel
from urllib.parse import urlencode
import json
from datetime import datetime

# Initialize pandarallel for parallel processing
pandarallel.initialize(progress_bar=False)

# Set page configuration
st.set_page_config(
    page_title="Commercial Real Estate Analytics",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add title and description
# st.title("Commercial Real Estate Hotspot Analysis")
# st.markdown("""
# This dashboard visualizes commercial real estate lease transactions from 2018-2024.
# Explore rental hotspots, market trends, and transaction patterns across different regions.
# """)

@st.cache_data(ttl=86400, show_spinner="📍Crunching loads of location data...")
def load_geocode_data():
    """Load the geocoding data from Geocodes.csv"""
    try:
        # Load the geocoding data
        geocode_df = pd.read_csv('data/Geocodes.csv', header=None)
        geocode_df.columns = ['address', 'coordinates']
        
        # Parse the coordinates string into separate lat and lon columns
        def parse_coordinates(coord_str):
            if pd.isna(coord_str):
                return np.nan, np.nan
            try:
                # Remove quotes and split by comma
                parts = coord_str.replace('"', '').split(',')
                if len(parts) >= 2:
                    return float(parts[1]), float(parts[0])
                return np.nan, np.nan
            except:
                return np.nan, np.nan
        
        # Extract lat and lon from coordinates
        geocode_df['lat_lon'] = geocode_df['coordinates'].parallel_apply(parse_coordinates)
        geocode_df['lat'] = geocode_df['lat_lon'].apply(lambda x: x[0] if isinstance(x, tuple) else np.nan)
        geocode_df['lon'] = geocode_df['lat_lon'].apply(lambda x: x[1] if isinstance(x, tuple) else np.nan)
        geocode_df.drop('lat_lon', axis=1, inplace=True)
        
        # Create a clean address format for matching
        geocode_df['clean_address'] = geocode_df['address'].str.replace('"', '').str.strip()
        
        # Return only records with valid coordinates
        return geocode_df.dropna(subset=['lat', 'lon'])
    except Exception as e:
        st.warning(f"Error loading geocode data: {e}. Will use estimated coordinates.")
        return pd.DataFrame(columns=['address', 'clean_address', 'lat', 'lon'])

@st.cache_data(ttl=86400, show_spinner="📊 Loading lease data...")
def load_data():
    """Load the lease data and perform initial processing"""
    try:
        df = pd.read_csv('data/Leases_with_coords.csv')
        # Convert columns to appropriate types
        if 'year' in df.columns:
            df['year'] = df['year'].astype(str)
        if 'quarter' in df.columns:
            df['quarter'] = df['quarter'].astype(str)
        if 'leasedSF' in df.columns:
            df['leasedSF'] = pd.to_numeric(df['leasedSF'], errors='coerce')
        if 'transaction_type' in df.columns:
            # Convert all transaction_type values to strings to avoid comparison errors
            df['transaction_type'] = df['transaction_type'].astype(str)
        
        # Create a datetime column for time series analysis if possible
        if 'year' in df.columns and 'quarter' in df.columns:
            df['period'] = df['year'] + '-Q' + df['quarter'].str.replace('Q', '')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Create a function to generate unique building keys and assign coordinates
@st.cache_data(ttl=86400, show_spinner="📍Crunching loads of location data...")
def prepare_building_data(df):
    """
    Process the dataframe to create a building-level dataset with coordinates
    """
    # Create a unique building identifier combining address and building_id
    df['building_key'] = df['building_id'].astype(str) + '_' + df['address'].astype(str)
    
    # Aggregate data to building level
    building_data = df.groupby(['building_key', 'building_name', 'address', 'city', 'state', 'zip']).agg({
        'leasedSF': 'sum',
        'costarID': 'count',
        'year': 'nunique'  # number of years with transactions
    }).reset_index()
    
    building_data = building_data.rename(columns={
        'leasedSF': 'total_leased_area',
        'costarID': 'num_transactions',
        'year': 'years_active'
    })
    
    # Load the geocode data
    geocode_df = load_geocode_data()
    
    # Create a more comprehensive geocoding dictionary with major US cities
    # (to use as fallback for addresses not found in geocode_df)
    geocode_dict = {
        # Major East Coast Cities
        "New York": {"lat": 40.7128, "lon": -74.0060},
        "Boston": {"lat": 42.3601, "lon": -71.0589},
        "Philadelphia": {"lat": 39.9526, "lon": -75.1652},
        "Washington": {"lat": 38.9072, "lon": -77.0369},
        "Baltimore": {"lat": 39.2904, "lon": -76.6122},
        
        # Southern Cities
        "Atlanta": {"lat": 33.7490, "lon": -84.3880},
        "Miami": {"lat": 25.7617, "lon": -80.1918},
        "Tampa": {"lat": 27.9506, "lon": -82.4572},
        "Orlando": {"lat": 28.5383, "lon": -81.3792},
        "Dallas": {"lat": 32.7767, "lon": -96.7970},
        "Houston": {"lat": 29.7604, "lon": -95.3698},
        "Austin": {"lat": 30.2672, "lon": -97.7431},
        "Nashville": {"lat": 36.1627, "lon": -86.7816},
        "Charlotte": {"lat": 35.2271, "lon": -80.8431},
        "Raleigh": {"lat": 35.7796, "lon": -78.6382},
        
        # Midwest Cities
        "Chicago": {"lat": 41.8781, "lon": -87.6298},
        "Detroit": {"lat": 42.3314, "lon": -83.0458},
        "Minneapolis": {"lat": 44.9778, "lon": -93.2650},
        "St. Louis": {"lat": 38.6270, "lon": -90.1994},
        "Denver": {"lat": 39.7392, "lon": -104.9903},
        
        # West Coast Cities
        "Los Angeles": {"lat": 34.0522, "lon": -118.2437},
        "San Francisco": {"lat": 37.7749, "lon": -122.4194},
        "San Diego": {"lat": 32.7157, "lon": -117.1611},
        "Seattle": {"lat": 47.6062, "lon": -122.3321},
        "Portland": {"lat": 45.5152, "lon": -122.6784},
        "Phoenix": {"lat": 33.4484, "lon": -112.0740},
        "Salt Lake City": {"lat": 40.7608, "lon": -111.8910},
        
        # Additional metros
        "San Jose": {"lat": 37.3382, "lon": -121.8863},
        "Oakland": {"lat": 37.8044, "lon": -122.2712},
        "Jersey City": {"lat": 40.7178, "lon": -74.0431},
        "Newark": {"lat": 40.7357, "lon": -74.1724},
        "Fort Lauderdale": {"lat": 26.1224, "lon": -80.1373},
        "Fort Worth": {"lat": 32.7555, "lon": -97.3308}
    }
    
    # Function to assign coordinates using geocode data or city-based fallback
    def assign_building_coordinates(row):
        # First, try to find exact match in geocoding data
        if not geocode_df.empty:
            # Prepare address for matching
            address = row['address']
            city = row['city'] if not pd.isna(row['city']) else ""
            state = row['state'] if not pd.isna(row['state']) else ""
            zip_code = str(row['zip']) if not pd.isna(row['zip']) else ""
            
            # Create different address formats to try matching
            address_formats = [
                f"{address}, {city}, {state}, {zip_code}",  # Full format
                f"{address}, {city}, {state}",              # Without zip
                address                                     # Just address
            ]
            
            # Try to find match for any of the address formats
            for addr_format in address_formats:
                addr_format = addr_format.strip().strip(',')
                match = geocode_df[geocode_df['clean_address'].str.contains(addr_format, case=False, regex=False, na=False)]
                
                if not match.empty:
                    # Found an address match - use the actual geocoding data
                    lat = match.iloc[0]['lat']
                    lon = match.iloc[0]['lon']
                    return lat, lon
        
        # # No match found in geocode data, fall back to city-based approach
        # city_name = row['city']
        # base_coords = None
        
        # # Check direct match
        # if city_name in geocode_dict:
        #     base_coords = geocode_dict[city_name]
        # else:
        #     # Try to match with partial city name (for cases like "San Francisco CBD")
        #     for known_city in geocode_dict.keys():
        #         if known_city in city_name:
        #             base_coords = geocode_dict[known_city]
        #             break
        
        # # If we found city coordinates, add some randomness to distribute buildings
        # if base_coords:
        #     # Add small random offsets (about 0.01 degrees ~ roughly 1km)
        #     # Use building_key hash to ensure consistent randomization for the same building
        #     seed = int(hash(row['building_key']) % 10000)
        #     np.random.seed(seed)
            
        #     # Scale the randomness by city size (larger offsets for bigger cities)
        #     # scale_factor = 0.02 if city_name in ["New York", "Los Angeles", "Chicago"] else 0.01
        #     scale_factor = 0.01
            
        #     lat_offset = np.random.uniform(-scale_factor, scale_factor)
        #     lon_offset = np.random.uniform(-scale_factor, scale_factor)
            
        #     return base_coords['lat'] + lat_offset, base_coords['lon'] + lon_offset
        
        return np.nan, np.nan
    
    # Apply the function to assign coordinates
    building_data['lat_lon'] = building_data.parallel_apply(assign_building_coordinates, axis=1)
    building_data['lat'] = building_data['lat_lon'].apply(lambda x: x[0] if isinstance(x, tuple) else np.nan)
    building_data['lon'] = building_data['lat_lon'].apply(lambda x: x[1] if isinstance(x, tuple) else np.nan)
    building_data.drop('lat_lon', axis=1, inplace=True)
    
    # Filter out buildings without coordinates
    geo_data = building_data.dropna(subset=['lat', 'lon'])
    
    return geo_data

# Create a function to generate unique building keys and assign coordinates
@st.cache_data(ttl=86400, show_spinner="📍Crunching loads of location data...")
def prepare_building_data_with_coords(df):
    """
    Process the dataframe to create a building-level dataset with coordinates
    """
    # Create a unique building identifier combining address and building_id
    df['building_key'] = df['building_id'].astype(str) + '_' + df['address'].astype(str)
    
    # Aggregate data to building level
    building_data = df.groupby(['building_key', 'building_name', 'address', 'city', 'state', 'zip']).agg({
        'leasedSF': 'sum',
        'costarID': 'count',
        'year': 'nunique',  # number of years with transactions
        'lat': 'first',     # take the first latitude value for each building
        'lon': 'first'      # take the first longitude value for each building
    }).reset_index()
    
    building_data = building_data.rename(columns={
        'leasedSF': 'total_leased_area',
        'costarID': 'num_transactions',
        'year': 'years_active'
    })
    
    # Filter out buildings without coordinates
    geo_data = building_data.dropna(subset=['lat', 'lon'])
    
    return geo_data

def get_query_params():
    """Get current query parameters from URL"""
    query_params = st.query_params
    return query_params

def set_query_params(**kwargs):
    """Set query parameters in URL"""
    st.query_params.update(kwargs)

def get_filter_from_params(param_name, options, default=None):
    """Extract filter values from query parameters"""
    params = get_query_params()
    
    if param_name in params:
        # Get values from URL
        param_values = params[param_name]
        # Filter only valid options
        valid_values = [val for val in param_values if val in options]
        return valid_values if valid_values else default
    return default

# Load data
with st.spinner("Loading data... (This may take a moment for large files)"):
    df = load_data()

if df is not None:
    # Display basic stats in the sidebar
    st.sidebar.header("Data Filters")
    
    # Year filter
    years = sorted(df['year'].unique()) if 'year' in df.columns else []
    default_years = get_filter_from_params('years', years, default=years)
    selected_years = st.sidebar.multiselect("Select Years", years, default=default_years)
    
    # Region filter
    regions = sorted(df['region'].unique()) if 'region' in df.columns else []
    default_regions = get_filter_from_params('regions', regions, default=None)
    selected_regions = st.sidebar.multiselect("Select Regions", regions, default=default_regions)
    
    # Market filter
    markets = sorted(df['market'].unique()) if 'market' in df.columns else []
    default_markets = get_filter_from_params('markets', markets, default=None)
    selected_markets = st.sidebar.multiselect("Select Markets", markets, default=default_markets)
    
    # Transaction type filter - Fixed by ensuring all values are strings
    transaction_types = sorted(df['transaction_type'].unique()) if 'transaction_type' in df.columns else []
    default_transaction_types = get_filter_from_params('transaction_types', transaction_types, default=None)
    selected_transaction_types = st.sidebar.multiselect("Select Transaction Types", transaction_types, default=default_transaction_types)

    # Update URL with current filter selections
    # Only include non-empty selections to keep URL clean
    url_params = {}
    if selected_years:
        url_params['years'] = selected_years
    if selected_regions:
        url_params['regions'] = selected_regions
    if selected_markets:
        url_params['markets'] = selected_markets
    if selected_transaction_types:
        url_params['transaction_types'] = selected_transaction_types
    
    # Update URL without triggering a rerun
    set_query_params(**url_params)

    # Apply filters
    filtered_df = df.copy()
    if selected_years:
        filtered_df = filtered_df[filtered_df['year'].isin(selected_years)]
    if selected_regions:
        filtered_df = filtered_df[filtered_df['region'].isin(selected_regions)]
    if selected_markets:
        filtered_df = filtered_df[filtered_df['market'].isin(selected_markets)]
    if selected_transaction_types:
        filtered_df = filtered_df[filtered_df['transaction_type'].isin(selected_transaction_types)]

    # Display data overview
    st.header("Data Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Transactions", f"{filtered_df.shape[0]:,}")
    with col2:
        total_leased_area = filtered_df['leasedSF'].sum() if 'leasedSF' in filtered_df.columns else 0
        st.metric("Total Leased Area (sq ft)", f"{total_leased_area:,.0f}")
    with col3:
        avg_lease_size = filtered_df['leasedSF'].mean() if 'leasedSF' in filtered_df.columns else 0
        st.metric("Avg Lease Size (sq ft)", f"{avg_lease_size:,.0f}")
    with col4:
        unique_buildings = filtered_df['building_id'].nunique() if 'building_id' in filtered_df.columns else 0
        st.metric("Unique Buildings", f"{unique_buildings:,}")
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Regional Hotspots", "Market Trends", "Transaction Analysis", "Data Explorer"])
    
    with tab1:
        # st.header("Regional Hotspot Map")
        
        # Create a map visualization at building level
        if 'address' in filtered_df.columns and 'building_id' in filtered_df.columns:
            # Prepare building-level data with coordinates
            building_geo_data = prepare_building_data_with_coords(filtered_df)
            
            if not building_geo_data.empty:
                # Create a map with PyDeck
                st.subheader("Lease Transaction Hotspots by Total Leased Area")
                
                # Let user choose between showing individual buildings or a heatmap
                map_view_type = st.radio(
                    "Select Map View Type:",
                    ["Heatmap", "Building Points"],
                    horizontal=True
                )
                
                # Create the view state
                # view_state = pdk.ViewState(
                #     latitude=building_geo_data['lat'].mean(),
                #     longitude=building_geo_data['lon'].mean(),
                #     zoom=None,
                #     pitch=45 if map_view_type == "3D Building Columns" else 0
                # )

                # Use compute_view 
                view_state = pdk.data_utils.compute_view(building_geo_data[['lon', 'lat']])
                # Create layers based on selected view type

                layers = []
                
                if map_view_type == "Building Points":
                    # Create scatter plot layer for buildings
                    scatter_layer = pdk.Layer(
                        "ScatterplotLayer",
                        data=building_geo_data,
                        get_position=['lon', 'lat'],
                        get_radius='20',
                        get_fill_color=[
                            "255 * (num_transactions > 10) + 140 * (num_transactions <= 10)", 
                            "140 * (num_transactions > 5) + 0 * (num_transactions <= 5)", 
                            "0", 
                            "140"
                        ],
                        pickable=True,
                        opacity=0.8,
                        stroked=True,
                        filled=True
                    )
                    layers.append(scatter_layer)
                    
                elif map_view_type == "Heatmap":
                    # Create heatmap layer
                    heatmap_layer = pdk.Layer(
                        "HeatmapLayer",
                        data=building_geo_data,
                        get_position=['lon', 'lat'],
                        get_weight='total_leased_area',
                        aggregation='SUM',
                        threshold=0.05,
                        pickable=False,
                        opacity=0.8
                    )
                    layers.append(heatmap_layer)
                    
                else:  # 3D Building Columns
                    # Create column layer for 3D visualization
                    column_layer = pdk.Layer(
                        "ColumnLayer",
                        data=building_geo_data,
                        get_position=['lon', 'lat'],
                        get_elevation='total_leased_area',
                        elevation_scale=0.00005,  # Adjust scale for better visualization
                        radius=100,  # Smaller radius for building-level detail
                        get_fill_color=[255, 140, 0, 140],
                        pickable=True,
                        auto_highlight=True
                    )
                    layers.append(column_layer)
                
                # Create tooltip
                tooltip = {
                    "html": "<b>{building_name}</b><br/>"
                           "{address}, {city}, {state} {zip}<br/>"
                           "Total Leased Area: {total_leased_area} sq ft<br/>"
                           "Number of Transactions: {num_transactions}<br/>"
                           "Years Active: {years_active}",
                    "style": {
                        "backgroundColor": "steelblue",
                        "color": "white"
                    }
                }
                
                # Create deck
                r = pdk.Deck(
                    layers=layers,
                    initial_view_state=view_state,
                    tooltip=tooltip
                )
                
                st.pydeck_chart(r)
                
                # Display top buildings table
                st.subheader("Top Buildings by Lease Activity")
                top_buildings = building_geo_data.sort_values(by='total_leased_area', ascending=False).head(10)
                
                # Rename columns for display
                display_df = top_buildings.copy()
                display_df = display_df.rename(columns={
                    'building_name': 'Building Name',
                    'address': 'Address',
                    'city': 'City',
                    'state': 'State',
                    'total_leased_area': 'Total Leased Area (sq ft)', 
                    'num_transactions': 'Number of Transactions',
                    'years_active': 'Years Active'
                })
                
                st.dataframe(display_df[['Building Name', 'Address', 'City', 'State', 
                                     'Total Leased Area (sq ft)', 'Number of Transactions', 'Years Active']])
            else:
                st.warning("No geographic data available for mapping with the current filters.")

    with tab2:
        st.header("Market Trends")
        
        # Plot 1: Trend of lease transactions over time
        if 'year' in filtered_df.columns and 'quarter' in filtered_df.columns:
            st.subheader("Lease Transaction Volume Over Time")
            
            # Create time-based grouping
            time_df = filtered_df.groupby(['year', 'quarter']).agg({
                'leasedSF': 'sum',
                'costarID': 'count'
            }).reset_index()
            
            time_df['period'] = time_df['year'] + '-Q' + time_df['quarter'].str.replace('Q', '')
            time_df = time_df.sort_values('period')
            
            # Create plotly chart for time series
            fig1 = px.line(
                time_df, x='period', y='leasedSF',
                title='Total Leased Area by Quarter',
                labels={'period': 'Quarter', 'leasedSF': 'Total Leased Area (sq ft)'}
            )
            
            fig2 = px.line(
                time_df, x='period', y='costarID',
                title='Number of Transactions by Quarter',
                labels={'period': 'Quarter', 'costarID': 'Number of Transactions'}
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                st.plotly_chart(fig2, use_container_width=True)
            
            # Regional comparison
            if 'region' in filtered_df.columns:
                st.subheader("Regional Market Comparison")
                
                region_time_df = filtered_df.groupby(['region', 'year']).agg({
                    'leasedSF': 'sum',
                    'costarID': 'count'
                }).reset_index()
                
                fig3 = px.bar(
                    region_time_df, x='year', y='leasedSF', color='region',
                    title='Leased Area by Region Over Time',
                    labels={'year': 'Year', 'leasedSF': 'Total Leased Area (sq ft)', 'region': 'Region'}
                )
                
                st.plotly_chart(fig3, use_container_width=True)
                
                # Average lease size by region
                region_avg_df = filtered_df.groupby('region').agg({
                    'leasedSF': 'mean'
                }).reset_index().sort_values('leasedSF', ascending=False)
                
                fig4 = px.bar(
                    region_avg_df, x='region', y='leasedSF',
                    title='Average Lease Size by Region',
                    labels={'region': 'Region', 'leasedSF': 'Average Lease Size (sq ft)'}
                )
                
                st.plotly_chart(fig4, use_container_width=True)
    
    with tab3:
        st.header("Transaction Analysis")
        
        # Transaction type distribution
        if 'transaction_type' in filtered_df.columns:
            st.subheader("Transaction Type Distribution")
            
            # Create summary for transaction types
            trans_df = filtered_df.groupby('transaction_type').agg({
                'leasedSF': 'sum',
                'costarID': 'count'
            }).reset_index()
            
            # Calculate percentages
            trans_df['Percentage of Transactions'] = trans_df['costarID'] / trans_df['costarID'].sum() * 100
            trans_df['Percentage of Area'] = trans_df['leasedSF'] / trans_df['leasedSF'].sum() * 100
            
            fig5 = px.pie(
                trans_df, values='costarID', names='transaction_type',
                title='Distribution of Transaction Types (by Count)'
            )
            
            fig6 = px.pie(
                trans_df, values='leasedSF', names='transaction_type',
                title='Distribution of Transaction Types (by Leased Area)'
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig5, use_container_width=True)
            with col2:
                st.plotly_chart(fig6, use_container_width=True)
            
            # Display transaction type data
            trans_df = trans_df.sort_values('leasedSF', ascending=False)
            st.dataframe(trans_df.rename(columns={
                'leasedSF': 'Total Leased Area (sq ft)',
                'costarID': 'Number of Transactions'
            }))
        
        # Internal class analysis
        if 'internal_class' in filtered_df.columns:
            st.subheader("Property Class Analysis")
            
            class_df = filtered_df.groupby('internal_class').agg({
                'leasedSF': ['sum', 'mean'],
                'costarID': 'count'
            })
            
            class_df.columns = ['Total Leased Area (SF)', 'Average Lease Size (SF)', 'Number of Transactions']
            class_df = class_df.reset_index()
            
            fig7 = px.bar(
                class_df, x='internal_class', y='Total Leased Area (SF)',
                title='Total Leased Area by Property Class',
                labels={'internal_class': 'Property Class'}
            )
            
            fig8 = px.bar(
                class_df, x='internal_class', y='Average Lease Size (SF)',
                title='Average Lease Size by Property Class',
                labels={'internal_class': 'Property Class'}
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig7, use_container_width=True)
            with col2:
                st.plotly_chart(fig8, use_container_width=True)
    
    with tab4:
        st.header("Data Explorer")
        
        # Allow users to select columns to view
        all_columns = df.columns.tolist()
        selected_columns = st.multiselect("Select Columns to Display", all_columns, 
                                         default=['year', 'quarter', 'market', 'city', 'state', 'internal_class', 
                                                 'leasedSF', 'company_name', 'transaction_type'])
        
        if selected_columns:
            st.dataframe(filtered_df[selected_columns])
        
        # Download option
        st.download_button(
            label="Download Filtered Data as CSV",
            data=filtered_df[selected_columns].to_csv(index=False).encode('utf-8'),
            file_name="filtered_lease_data.csv",
            mime="text/csv",
        )
else:
    st.error("Failed to load lease data. Please check if the file exists and is accessible.")
    st.info("Please make sure 'data/Leases.csv' is available in the correct location.")