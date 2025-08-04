import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
import sqlite3
import hashlib
import json
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Set page configuration
st.set_page_config(
    page_title="Personal Investment Journal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Sky Blue Theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #0EA5E9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .portfolio-card {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #BAE6FD;
        margin-bottom: 20px;
    }
    
    .positive {
        color: #10B981;
        font-weight: bold;
    }
    
    .negative {
        color: #EF4444;
        font-weight: bold;
    }
    
    .login-form {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #BAE6FD;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        max-width: 400px;
        margin: 50px auto;
    }
    
    .stButton > button {
        background: #0EA5E9;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: 500;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: #0284C7;
    }
    
    .user-info {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

class UserAuth:
    def __init__(self):
        self.init_user_database()
    
    def init_user_database(self):
        """Initialize user authentication database"""
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_date DATE DEFAULT CURRENT_DATE,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create user sessions table for session management
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, email: str, password: str, full_name: str) -> bool:
        """Create a new user"""
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            c.execute('''
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, full_name))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user info"""
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        password_hash = self.hash_password(password)
        
        c.execute('''
            SELECT id, username, email, full_name, is_active
            FROM users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
        ''', (username, password_hash))
        
        user = c.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[3],
                'is_active': user[4]
            }
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user information by ID"""
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT id, username, email, full_name, is_active
            FROM users 
            WHERE id = ? AND is_active = 1
        ''', (user_id,))
        
        user = c.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[3],
                'is_active': user[4]
            }
        return None

class InvestmentJournal:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with user-specific data"""
        conn = sqlite3.connect('investment_journal.db')
        c = conn.cursor()
        
        # Create portfolios table with user_id
        c.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create transactions table with user_id
        c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                portfolio_id INTEGER,
                symbol TEXT NOT NULL,
                stock_name TEXT,
                type TEXT CHECK(type IN ('Stock', 'MF')),
                action TEXT CHECK(action IN ('Buy', 'Sell')),
                date DATE NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                transaction_price REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_portfolio(self, name: str, description: str = ""):
        """Add a new portfolio for the current user"""
        conn = sqlite3.connect('investment_journal.db')
        c = conn.cursor()
        c.execute("INSERT INTO portfolios (user_id, name, description) VALUES (?, ?, ?)", 
                 (self.user_id, name, description))
        conn.commit()
        conn.close()
    
    def get_portfolios(self) -> pd.DataFrame:
        """Get all portfolios for the current user"""
        conn = sqlite3.connect('investment_journal.db')
        df = pd.read_sql_query("SELECT * FROM portfolios WHERE user_id = ?", conn, params=(self.user_id,))
        conn.close()
        return df
    
    def add_transaction(self, portfolio_id: int, symbol: str, stock_name: str, 
                       type_: str, action: str, date_: str, quantity: int, 
                       price: float, transaction_price: float):
        """Add a new transaction for the current user"""
        conn = sqlite3.connect('investment_journal.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO transactions (user_id, portfolio_id, symbol, stock_name, type, action, date, quantity, price, transaction_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.user_id, portfolio_id, symbol, stock_name, type_, action, date_, quantity, price, transaction_price))
        conn.commit()
        conn.close()
    
    def get_transactions(self, portfolio_id: Optional[int] = None) -> pd.DataFrame:
        """Get transactions for the current user and optionally for a specific portfolio"""
        conn = sqlite3.connect('investment_journal.db')
        if portfolio_id:
            df = pd.read_sql_query("SELECT * FROM transactions WHERE user_id = ? AND portfolio_id = ?", 
                                 conn, params=(self.user_id, portfolio_id))
        else:
            df = pd.read_sql_query("SELECT * FROM transactions WHERE user_id = ?", conn, params=(self.user_id,))
        conn.close()
        return df
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_stock_info(_self, symbol: str) -> Dict:
        """Get stock information using yfinance"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return {
                'name': info.get('longName', symbol),
                'price': info.get('currentPrice', 0),
                'currency': info.get('currency', 'INR')
            }
        except:
            return {'name': symbol, 'price': 0, 'currency': 'INR'}
    
    @st.cache_data(ttl=300)
    def get_current_price(_self, symbol: str) -> float:
        """Get current stock price using yfinance"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            return 0.0
        except:
            return 0.0
    
    def calculate_xirr(self, cash_flows: List[Tuple[datetime, float]], guess: float = 0.1) -> float:
        """Calculate XIRR using Newton-Raphson method"""
        if len(cash_flows) < 2:
            return 0.0
        
        # Sort by date
        cash_flows.sort(key=lambda x: x[0])
        
        first_date = cash_flows[0][0]
        rate = guess
        
        for _ in range(100):  # Max iterations
            npv = 0
            dnpv = 0
            
            for date_val, amount in cash_flows:
                days_diff = (date_val - first_date).days
                years_frac = days_diff / 365.25
                factor = (1 + rate) ** years_frac
                
                npv += amount / factor
                dnpv -= amount * years_frac / (factor * (1 + rate))
            
            if abs(npv) < 1e-6:
                return rate
            
            if abs(dnpv) < 1e-6:
                break
            
            rate = rate - npv / dnpv
            
            # Prevent extreme values
            if rate < -0.99:
                rate = -0.99
            if rate > 10:
                rate = 10
        
        return rate
    
    def calculate_portfolio_stats(self, portfolio_id: Optional[int] = None) -> Dict:
        """Calculate portfolio statistics for the current user"""
        transactions = self.get_transactions(portfolio_id)
        
        if transactions.empty:
            return {
                'total_investment': 0,
                'current_value': 0,
                'total_gain_loss': 0,
                'total_gain_loss_pct': 0,
                'xirr': 0,
                'holdings': {}
            }
        
        # Calculate holdings
        holdings = {}
        cash_flows = []
        
        for _, tx in transactions.iterrows():
            symbol = tx['symbol']
            if symbol not in holdings:
                holdings[symbol] = {
                    'quantity': 0,
                    'total_investment': 0,
                    'name': tx['stock_name'],
                    'type': tx['type']
                }
            
            if tx['action'] == 'Buy':
                holdings[symbol]['quantity'] += tx['quantity']
                investment = tx['quantity'] * tx['transaction_price']
                holdings[symbol]['total_investment'] += investment
                cash_flows.append((datetime.strptime(tx['date'], '%Y-%m-%d'), -investment))
            else:
                holdings[symbol]['quantity'] -= tx['quantity']
                investment = tx['quantity'] * tx['transaction_price']
                holdings[symbol]['total_investment'] -= investment
                cash_flows.append((datetime.strptime(tx['date'], '%Y-%m-%d'), investment))
        
        # Calculate current values
        total_investment = 0
        current_value = 0
        
        for symbol, holding in holdings.items():
            if holding['quantity'] > 0:
                current_price = self.get_current_price(symbol)
                holding['current_price'] = current_price
                holding['current_value'] = holding['quantity'] * current_price
                holding['gain_loss'] = holding['current_value'] - holding['total_investment']
                holding['gain_loss_pct'] = (holding['gain_loss'] / holding['total_investment'] * 100) if holding['total_investment'] > 0 else 0
                
                total_investment += holding['total_investment']
                current_value += holding['current_value']
                
                # Add current value to cash flows for XIRR
                cash_flows.append((datetime.now(), holding['current_value']))
        
        # Calculate XIRR
        xirr = self.calculate_xirr(cash_flows) if len(cash_flows) >= 2 else 0
        
        return {
            'total_investment': total_investment,
            'current_value': current_value,
            'total_gain_loss': current_value - total_investment,
            'total_gain_loss_pct': ((current_value - total_investment) / total_investment * 100) if total_investment > 0 else 0,
            'xirr': xirr * 100,  # Convert to percentage
            'holdings': holdings
        }

def show_login_page():
    """Display login/register page"""
    st.markdown("""
    <div class="main-header">
        <h1>📈 Personal Investment Journal</h1>
        <p>Multi-User Investment Portfolio Tracker with XIRR Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for login and registration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="login-form">
            <h3>🔐 Login</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            login_button = st.form_submit_button("🚀 Login", type="primary")
            
            if login_button:
                if username and password:
                    auth = UserAuth()
                    user = auth.authenticate_user(username, password)
                    
                    if user:
                        st.session_state.user = user
                        st.session_state.is_authenticated = True
                        st.success(f"✅ Welcome back, {user['full_name']}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.error("❗ Please enter both username and password")
    
    with col2:
        st.markdown("""
        <div class="login-form">
            <h3>📝 Register</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("register_form"):
            reg_username = st.text_input("Username", key="reg_username")
            reg_email = st.text_input("Email", key="reg_email")
            reg_full_name = st.text_input("Full Name", key="reg_full_name")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")
            register_button = st.form_submit_button("✨ Create Account", type="primary")
            
            if register_button:
                if all([reg_username, reg_email, reg_full_name, reg_password, reg_password_confirm]):
                    if reg_password == reg_password_confirm:
                        if len(reg_password) >= 6:
                            auth = UserAuth()
                            if auth.create_user(reg_username, reg_email, reg_password, reg_full_name):
                                st.success("✅ Account created successfully! Please login.")
                            else:
                                st.error("❌ Username or email already exists")
                        else:
                            st.error("❗ Password must be at least 6 characters long")
                    else:
                        st.error("❗ Passwords do not match")
                else:
                    st.error("❗ Please fill in all fields")

def show_user_info():
    """Display user information in sidebar"""
    if 'user' in st.session_state:
        user = st.session_state.user
        st.sidebar.markdown(f"""
        <div class="user-info">
            <div><strong>👤 {user['full_name']}</strong></div>
            <div>📧 {user['email']}</div>
            <div>🏷️ @{user['username']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.sidebar.button("🚪 Logout", type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def main():
    # Initialize session state
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    
    if not st.session_state.is_authenticated:
        show_login_page()
        return
    
    # User is authenticated, show the main app
    show_user_info()
    
    # Initialize journal for current user
    user_id = st.session_state.user['id']
    journal = InvestmentJournal(user_id)
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>📈 Investment Journal - Welcome {st.session_state.user['full_name']}</h1>
        <p>Track, Analyze, and Optimize Your Investment Portfolio with XIRR Calculations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Navigation
    st.sidebar.title("🧭 Navigation")
    
    # Portfolio selector
    portfolios = journal.get_portfolios()
    if not portfolios.empty:
        portfolio_options = ["All Portfolios"] + [f"{row['name']} (ID: {row['id']})" for _, row in portfolios.iterrows()]
        selected_portfolio = st.sidebar.selectbox("📊 Select Portfolio", portfolio_options)
        
        if selected_portfolio == "All Portfolios":
            current_portfolio_id = None
        else:
            current_portfolio_id = int(selected_portfolio.split("ID: ")[1].split(")")[0])
    else:
        current_portfolio_id = None
    
    # Navigation
    page = st.sidebar.selectbox(
        "🚀 Go to",
        ["Dashboard", "Portfolios", "Add Transaction", "Holdings", "Performance", "Settings"]
    )
    
    if page == "Dashboard":
        show_dashboard(journal, current_portfolio_id)
    elif page == "Portfolios":
        show_portfolios(journal)
    elif page == "Add Transaction":
        show_add_transaction(journal)
    elif page == "Holdings":
        show_holdings(journal, current_portfolio_id)
    elif page == "Performance":
        show_performance(journal, current_portfolio_id)
    elif page == "Settings":
        show_settings(journal)

def show_dashboard(journal, portfolio_id):
    st.header("📊 Dashboard Overview")
    
    # Get portfolio stats
    stats = journal.calculate_portfolio_stats(portfolio_id)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>💰 Total Investment</h4>
            <h2>₹{stats['total_investment']:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>💎 Current Value</h4>
            <h2>₹{stats['current_value']:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        gain_loss_color = "positive" if stats['total_gain_loss'] >= 0 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <h4>📈 Total P&amp;L</h4>
            <h2 class="{gain_loss_color}">₹{stats['total_gain_loss']:,.2f}</h2>
            <p class="{gain_loss_color}">({stats['total_gain_loss_pct']:.2f}%)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        xirr_color = "positive" if stats['xirr'] >= 0 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <h4>🎯 XIRR</h4>
            <h2 class="{xirr_color}">{stats['xirr']:.2f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts and recent transactions
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥧 Portfolio Allocation")
        if stats['holdings']:
            labels = []
            values = []
            for symbol, holding in stats['holdings'].items():
                if holding['quantity'] > 0:
                    labels.append(holding['name'][:20])
                    values.append(holding['current_value'])
            
            if labels and values:
                fig = px.pie(
                    values=values,
                    names=labels,
                    title="Current Portfolio Allocation",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='%{label}<br>Value: ₹%{value:,.0f}<extra></extra>'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No holdings to display. Add your first transaction!")
    
    with col2:
        st.subheader("📝 Recent Transactions")
        transactions = journal.get_transactions(portfolio_id)
        if not transactions.empty:
            recent_tx = transactions.tail(5).sort_values('date', ascending=False)
            for _, tx in recent_tx.iterrows():
                action_color = "positive" if tx['action'] == 'Buy' else "negative" 
                st.markdown(f"""
                <div style="padding: 10px; border-left: 3px solid {'#10B981' if tx['action'] == 'Buy' else '#EF4444'}; margin: 5px 0; background: #F8FAFC; border-radius: 5px;">
                    <strong>{tx['stock_name']}</strong><br>
                    <span class="{action_color}">{tx['action']}</span> {tx['quantity']} @ ₹{tx['transaction_price']}<br>
                    <small>📅 {tx['date']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No transactions found. Add your first transaction!")

def show_portfolios(journal):
    st.header("💼 Portfolio Management")
    
    # Add new portfolio
    with st.expander("➕ Create New Portfolio"):
        with st.form("add_portfolio"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Portfolio Name*", placeholder="e.g., Growth Portfolio")
            with col2:
                description = st.text_area("Description", placeholder="Brief description of investment strategy")
            
            if st.form_submit_button("🚀 Create Portfolio", type="primary"):
                if name:
                    journal.add_portfolio(name, description)
                    st.success(f"✅ Portfolio '{name}' created successfully!")
                    st.rerun()
                else:
                    st.error("❗ Please enter a portfolio name")
    
    # Display existing portfolios
    portfolios = journal.get_portfolios()
    if not portfolios.empty:
        st.subheader("📋 Your Portfolios")
        
        for _, portfolio in portfolios.iterrows():
            stats = journal.calculate_portfolio_stats(portfolio['id'])
            
            st.markdown(f"""
            <div class="portfolio-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3>💼 {portfolio['name']}</h3>
                        <p>{portfolio['description']}</p>
                        <small>📅 Created: {portfolio['created_date']}</small>
                    </div>
                    <div style="text-align: right;">
                        <div><strong>Investment:</strong> ₹{stats['total_investment']:,.0f}</div>
                        <div><strong>Current Value:</strong> ₹{stats['current_value']:,.0f}</div>
                        <div class="{'positive' if stats['total_gain_loss'] >= 0 else 'negative'}"><strong>P&L:</strong> ₹{stats['total_gain_loss']:,.0f} ({stats['total_gain_loss_pct']:.1f}%)</div>
                        <div class="{'positive' if stats['xirr'] >= 0 else 'negative'}"><strong>XIRR:</strong> {stats['xirr']:.2f}%</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📝 No portfolios found. Create your first portfolio above!")

def show_add_transaction(journal):
    st.header("➕ Add New Transaction")
    
    portfolios = journal.get_portfolios()
    if portfolios.empty:
        st.error("❗ Please create a portfolio first!")
        return
    
    with st.form("add_transaction"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Portfolio & Investment Details")
            
            portfolio_id = st.selectbox(
                "Select Portfolio*",
                portfolios['id'].tolist(),
                format_func=lambda x: portfolios[portfolios['id']==x]['name'].iloc[0]
            )
            
            investment_type = st.selectbox("Investment Type*", ["Stock", "MF"])
            
            action = st.selectbox("Action*", ["Buy", "Sell"])
            
            transaction_date = st.date_input("Transaction Date*", value=date.today())
        
        with col2:
            st.subheader("💹 Stock & Pricing Details")
            
            symbol = st.text_input(
                "Stock/MF Symbol*", 
                placeholder="e.g., RELIANCE.NS, TCS.NS, INFY.NS",
                help="Use .NS suffix for NSE stocks, .BO for BSE"
            )
            
            quantity = st.number_input("Quantity*", min_value=1, value=1)
            
            transaction_price = st.number_input(
                "Transaction Price (₹)*", 
                min_value=0.01, 
                value=100.0, 
                step=0.01,
                help="The actual price you paid/received per share"
            )
        
        # Auto-fetch stock info
        if symbol:
            with st.spinner("🔍 Fetching stock information..."):
                stock_info = journal.get_stock_info(symbol)
                current_price = journal.get_current_price(symbol)
                
                st.info(f"**📈 Stock Name:** {stock_info['name']}")
                if current_price > 0:
                    st.info(f"**💰 Current Market Price:** ₹{current_price:.2f}")
                    price_diff = ((transaction_price - current_price) / current_price * 100) if current_price > 0 else 0
                    if abs(price_diff) > 5:
                        st.warning(f"⚠️ Your transaction price is {price_diff:+.1f}% from current market price")
        
        if st.form_submit_button("💾 Add Transaction", type="primary"):
            if symbol and quantity > 0 and transaction_price > 0:
                stock_info = journal.get_stock_info(symbol)
                current_price = journal.get_current_price(symbol)
                
                journal.add_transaction(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    stock_name=stock_info['name'],
                    type_=investment_type,
                    action=action,
                    date_=str(transaction_date),
                    quantity=quantity,
                    price=current_price,
                    transaction_price=transaction_price
                )
                
                st.success("✅ Transaction added successfully!")
                st.balloons()
                st.rerun()
            else:
                st.error("❗ Please fill all required fields")

def show_holdings(journal, portfolio_id):
    st.header("💰 Current Holdings")
    
    stats = journal.calculate_portfolio_stats(portfolio_id)
    
    if not stats['holdings']:
        st.info("📝 No holdings found. Add some transactions to see your holdings here!")
        return
    
    # Summary cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total Investment", f"₹{stats['total_investment']:,.0f}")
    with col2:
        st.metric("💎 Current Value", f"₹{stats['current_value']:,.0f}")
    with col3:
        st.metric("📈 Total P&L", f"₹{stats['total_gain_loss']:,.0f}", f"{stats['total_gain_loss_pct']:.2f}%")
    
    st.divider()
    
    # Create holdings data
    holdings_data = []
    for symbol, holding in stats['holdings'].items():
        if holding['quantity'] > 0:
            # Calculate individual XIRR
            transactions = journal.get_transactions(portfolio_id)
            holding_transactions = transactions[transactions['symbol'] == symbol]
            
            cash_flows = []
            for _, tx in holding_transactions.iterrows():
                amount = tx['quantity'] * tx['transaction_price']
                if tx['action'] == 'Buy':
                    amount = -amount
                cash_flows.append((datetime.strptime(tx['date'], '%Y-%m-%d'), amount))
            
            cash_flows.append((datetime.now(), holding['current_value']))
            individual_xirr = journal.calculate_xirr(cash_flows) * 100 if len(cash_flows) >= 2 else 0
            
            holdings_data.append({
                'Stock Name': holding['name'],
                'Type': holding['type'],
                'Symbol': symbol,
                'Quantity': holding['quantity'],
                'Avg Price': holding['total_investment'] / holding['quantity'],
                'Current Price': holding['current_price'],
                'Investment': holding['total_investment'],
                'Current Value': holding['current_value'],
                'P&L': holding['gain_loss'],
                'P&L %': holding['gain_loss_pct'],
                'XIRR %': individual_xirr
            })
    
    if holdings_data:
        st.subheader("📊 Detailed Holdings")
        
        for row in holdings_data:
            col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 2])
            
            with col1:
                st.markdown(f"""
                **{row['Stock Name']}**  
                {row['Symbol']} • {row['Type']}  
                Qty: {row['Quantity']}
                """)
            
            with col2:
                st.metric("Avg Price", f"₹{row['Avg Price']:.2f}")
                st.metric("Current", f"₹{row['Current Price']:.2f}")
            
            with col3:
                st.metric("Investment", f"₹{row['Investment']:,.0f}")
                st.metric("Current Value", f"₹{row['Current Value']:,.0f}")
            
            with col4:
                color = "normal" if row['P&L'] >= 0 else "inverse"
                st.metric("P&L", f"₹{row['P&L']:,.0f}", f"{row['P&L %']:.2f}%", delta_color=color)
            
            with col5:
                color = "normal" if row['XIRR %'] >= 0 else "inverse"
                st.metric("XIRR", f"{row['XIRR %']:.2f}%", delta_color=color)
            
            st.divider()

def show_performance(journal, portfolio_id):
    st.header("📈 Performance Analysis")
    
    # XIRR Summary
    st.subheader("🎯 XIRR Analysis Summary")
    
    xirr_data = []
    
    # Individual securities XIRR
    stats = journal.calculate_portfolio_stats(portfolio_id)
    for symbol, holding in stats['holdings'].items():
        if holding['quantity'] > 0:
            transactions = journal.get_transactions(portfolio_id)
            holding_transactions = transactions[transactions['symbol'] == symbol]
            
            cash_flows = []
            for _, tx in holding_transactions.iterrows():
                amount = tx['quantity'] * tx['transaction_price']
                if tx['action'] == 'Buy':
                    amount = -amount
                cash_flows.append((datetime.strptime(tx['date'], '%Y-%m-%d'), amount))
            
            cash_flows.append((datetime.now(), holding['current_value']))
            individual_xirr = journal.calculate_xirr(cash_flows) * 100 if len(cash_flows) >= 2 else 0
            
            xirr_data.append({
                'Name': holding['name'],
                'Type': f"Individual {holding['type']}",
                'XIRR (%)': individual_xirr,
                'Category': 'Security'
            })
    
    # Portfolio XIRR
    portfolios = journal.get_portfolios()
    if not portfolios.empty:
        for _, portfolio in portfolios.iterrows():
            portfolio_stats = journal.calculate_portfolio_stats(portfolio['id'])
            xirr_data.append({
                'Name': portfolio['name'],
                'Type': 'Portfolio',
                'XIRR (%)': portfolio_stats['xirr'],
                'Category': 'Portfolio'
            })
    
    # Total XIRR
    total_stats = journal.calculate_portfolio_stats(None)
    xirr_data.append({
        'Name': 'Total Portfolio',
        'Type': 'All Portfolios',
        'XIRR (%)': total_stats['xirr'],
        'Category': 'Total'
    })
    
    if xirr_data:
        xirr_df = pd.DataFrame(xirr_data)
        
        for category in ['Security', 'Portfolio', 'Total']:
            category_data = xirr_df[xirr_df['Category'] == category]
            if not category_data.empty:
                st.write(f"**{category} XIRR:**")
                
                for _, row in category_data.iterrows():
                    color = "🟢" if row['XIRR (%)'] >= 0 else "🔴"
                    st.markdown(f"{color} **{row['Name']}** ({row['Type']}): **{row['XIRR (%)']:.2f}%**")
                
                st.divider()

def show_settings(journal):
    st.header("⚙️ Settings & Data Management")
    
    st.subheader("👤 User Profile")
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Full Name:** {user['full_name']}")
        st.info(f"**Username:** {user['username']}")
    with col2:
        st.info(f"**Email:** {user['email']}")
        st.info(f"**User ID:** {user['id']}")
    
    st.divider()
    
    st.subheader("📤 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Portfolios", type="secondary"):
            portfolios = journal.get_portfolios()
            if not portfolios.empty:
                csv = portfolios.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download Portfolios CSV",
                    data=csv,
                    file_name=f"portfolios_{user['username']}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("📝 No portfolios to export")
    
    with col2:
        if st.button("📋 Export All Transactions", type="secondary"):
            transactions = journal.get_transactions()
            if not transactions.empty:
                csv = transactions.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download Transactions CSV",
                    data=csv,
                    file_name=f"transactions_{user['username']}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("📝 No transactions to export")
    
    st.divider()
    
    st.subheader("🗑️ Data Management")
    
    st.warning("⚠️ **Danger Zone** - These actions are irreversible!")
    
    if st.button("🗑️ Clear My Data", type="secondary"):
        if st.checkbox("✅ I understand this will delete all my portfolios and transactions"):
            conn = sqlite3.connect('investment_journal.db')
            c = conn.cursor()
            c.execute("DELETE FROM transactions WHERE user_id = ?", (journal.user_id,))
            c.execute("DELETE FROM portfolios WHERE user_id = ?", (journal.user_id,))
            conn.commit()
            conn.close()
            st.success("🧹 Your data cleared successfully!")
            st.rerun()

if __name__ == "__main__":
    main()