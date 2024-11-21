import streamlit as st

class AppStyle:
    # Color scheme
    COLORS = {
        'primary': '#1f77b4',
        'secondary': '#2ecc71',
        'warning': '#f1c40f',
        'danger': '#e74c3c',
        'success': '#2ecc71',
        'info': '#3498db',
        'light': '#ecf0f1',
        'dark': '#2c3e50',
        'white': '#ffffff',
        'black': '#000000',
        'gray': '#95a5a6',
        
        # Device-specific colors
        'ph': '#1f77b4',
        'ec': '#ff7f0e',
        'do': '#2ca02c',
        'rtd': '#d62728'
    }

    # Custom CSS
    CUSTOM_CSS = """
        <style>
        /* Main container styling */
        .main {
            background-color: #f8f9fa;
            padding: 2rem;
        }

        /* Card styling */
        .stCard {
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease-in-out;
        }
        
        .stCard:hover {
            transform: translateY(-2px);
        }

        /* Button styling */
        .stButton button {
            border-radius: 0.5rem;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Metric styling */
        .css-1xarl3l {
            background-color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        /* Device cards */
        .device-card {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 1px solid #e9ecef;
        }
        
        .device-card:hover {
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }

        /* Status indicators */
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }
        
        .status-active {
            background-color: #2ecc71;
        }
        
        .status-inactive {
            background-color: #e74c3c;
        }

        /* Reading displays */
        .reading-display {
            font-size: 2rem;
            font-weight: 600;
            color: #2c3e50;
            text-align: center;
            padding: 1rem;
            background: white;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        /* Progress bars */
        .stProgress > div > div > div {
            background-color: #1f77b4;
            border-radius: 1rem;
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
            padding: 0.5rem;
            background-color: white;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            padding: 0 1.5rem;
            border-radius: 0.5rem;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #1f77b4 !important;
            color: white !important;
        }

        /* Form inputs */
        .stTextInput input, .stNumberInput input {
            border-radius: 0.5rem;
            border: 1px solid #ced4da;
            padding: 0.5rem 1rem;
        }
        
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: #1f77b4;
            box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2);
        }

        /* Select boxes */
        .stSelectbox select {
            border-radius: 0.5rem;
            border: 1px solid #ced4da;
            padding: 0.5rem 1rem;
        }

        /* Charts */
        .chart-container {
            background: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        /* Tables */
        .dataframe {
            border: none !important;
            border-collapse: collapse !important;
            width: 100% !important;
        }
        
        .dataframe th {
            background-color: #f8f9fa !important;
            padding: 0.75rem !important;
            font-weight: 600 !important;
            border-bottom: 2px solid #dee2e6 !important;
        }
        
        .dataframe td {
            padding: 0.75rem !important;
            border-bottom: 1px solid #dee2e6 !important;
        }
        
        .dataframe tr:hover {
            background-color: #f8f9fa !important;
        }

        /* Alerts */
        .success-alert {
            background-color: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #c3e6cb;
            margin: 1rem 0;
        }
        
        .error-alert {
            background-color: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #f5c6cb;
            margin: 1rem 0;
        }
        
        .info-alert {
            background-color: #cce5ff;
            color: #004085;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #b8daff;
            margin: 1rem 0;
        }

        /* Device type badges */
        .device-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.875rem;
            font-weight: 500;
            margin-right: 0.5rem;
        }
        
        .device-badge-ph {
            background-color: rgba(31, 119, 180, 0.1);
            color: #1f77b4;
        }
        
        .device-badge-ec {
            background-color: rgba(255, 127, 14, 0.1);
            color: #ff7f0e;
        }
        
        .device-badge-do {
            background-color: rgba(44, 160, 44, 0.1);
            color: #2ca02c;
        }
        
        .device-badge-rtd {
            background-color: rgba(214, 39, 40, 0.1);
            color: #d62728;
        }
        </style>
    """

    @staticmethod
    def apply_style():
        """Apply custom styling to the Streamlit app"""
        st.markdown(AppStyle.CUSTOM_CSS, unsafe_allow_html=True)

    @staticmethod
    def device_card(device_type, title, content):
        """Create a styled device card"""
        html = f"""
        <div class="device-card">
            <div class="device-badge device-badge-{device_type.lower()}">{device_type.upper()}</div>
            <h3>{title}</h3>
            <div>{content}</div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    @staticmethod
    def status_indicator(status):
        """Create a status indicator"""
        status_class = "status-active" if status else "status-inactive"
        html = f"""
        <div class="status-indicator {status_class}"></div>
        <span>{status and "Active" or "Inactive"}</span>
        """
        st.markdown(html, unsafe_allow_html=True)

    @staticmethod
    def reading_display(value, unit):
        """Create a styled reading display"""
        html = f"""
        <div class="reading-display">
            <span>{value}</span>
            <span style="font-size: 1rem; color: #95a5a6;">{unit}</span>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    @staticmethod
    def alert(message, alert_type="info"):
        """Create a styled alert"""
        html = f"""
        <div class="{alert_type}-alert">
            {message}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

def apply_plot_style(fig):
    """Apply consistent styling to plotly figures"""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'sans-serif'},
        title_font_size=20,
        title_font_family='sans-serif',
        title_font_color='#2c3e50',
        legend_title_font_size=12,
        legend_font_size=10,
        margin=dict(t=50, l=50, r=20, b=50),
    )
    
    fig.update_xaxes(
        gridcolor='#ecf0f1',
        zeroline=False,
    )
    
    fig.update_yaxes(
        gridcolor='#ecf0f1',
        zeroline=False,
    )
    
    return fig

# Usage in your app
def init_styling():
    """Initialize all styling for the app"""
    AppStyle.apply_style()

/* Verification cards */
    .verification-good {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    
    .verification-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    
    .verification-good .value,
    .verification-warning .value {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .verification-good .status,
    .verification-warning .status {
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .verification-good .range,
    .verification-warning .range {
        font-size: 0.875rem;
        opacity: 0.8;
    }
