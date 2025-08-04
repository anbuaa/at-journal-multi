# Personal Investment Journal

A comprehensive multi-user investment portfolio tracking application built with Streamlit, featuring advanced XIRR calculations, real-time stock price updates, and performance analysis.

## 🚀 Features

### 👥 Multi-User Authentication
- Secure user registration and login system
- Password hashing with SHA-256 encryption
- User data isolation and session management
- Individual user dashboards and portfolios

### 💼 Portfolio Management
- Create and manage multiple investment portfolios
- Track stocks and mutual funds separately
- Real-time portfolio valuation using Yahoo Finance
- Comprehensive transaction history

### 📊 Advanced Analytics
- **XIRR Calculations**: Individual security, portfolio, and total portfolio XIRR
- **Performance Metrics**: P&L tracking, percentage returns
- **Benchmark Comparison**: Compare portfolio performance with market indices
- **Interactive Charts**: Portfolio allocation and performance visualization

### 🎨 Modern UI/UX
- Beautiful sky blue theme with gradient backgrounds
- Responsive design for desktop and mobile
- Dark/light mode support
- Professional dashboard with interactive elements

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Streamlit with custom CSS styling
- **Backend**: Python with SQLite database
- **Data Source**: Yahoo Finance (yfinance)
- **Visualization**: Plotly for interactive charts
- **Authentication**: Custom implementation with secure password hashing

### Database Schema
```sql
-- Users table
users (id, username, email, password_hash, full_name, created_date, is_active)

-- Portfolios table
portfolios (id, user_id, name, description, created_date)

-- Transactions table
transactions (id, user_id, portfolio_id, symbol, stock_name, type, action, 
              date, quantity, price, transaction_price)
```

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git (for cloning the repository)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/investment-journal.git
   cd investment-journal
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the application**
   - Open your browser and navigate to `http://localhost:8501`
   - Register a new account or login with existing credentials

## 🐳 Docker Deployment

### Quick Start with Docker
```bash
# Build and run the container
docker build -t investment-journal .
docker run -p 8501:8501 investment-journal
```

### Production Deployment with Docker Compose
```bash
# Start all services (app + nginx)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🌐 Production Deployment

### Option 1: Streamlit Community Cloud (Free)
1. Push your code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy with one click

### Option 2: VPS Deployment
See the detailed [Deployment Guide](docs/deployment-guide.md) for:
- VPS setup and configuration
- NGINX reverse proxy setup
- SSL certificate installation
- Process management with PM2
- Monitoring and backup strategies

### Option 3: Cloud Platforms
- **AWS EC2**: Enterprise-grade hosting
- **Azure App Service**: Managed platform
- **Google Cloud Run**: Serverless deployment
- **DigitalOcean**: Developer-friendly VPS

## 📊 Usage Guide

### Getting Started
1. **Create Account**: Register with username, email, and password
2. **Create Portfolio**: Set up your first investment portfolio
3. **Add Transactions**: Record buy/sell transactions with actual prices
4. **Monitor Performance**: Track real-time portfolio performance and XIRR

### Adding Transactions
- Select portfolio and investment type (Stock/MF)
- Enter stock symbol (e.g., RELIANCE.NS for NSE stocks)
- Specify quantity and transaction price
- System auto-fetches current market price and stock name

### Portfolio Analysis
- **Dashboard**: Overview of all portfolios with key metrics
- **Holdings**: Detailed view of current positions with P&L
- **Performance**: XIRR analysis and benchmark comparison
- **Export**: Download portfolio and transaction data as CSV

### Supported Markets
- **Indian Stocks**: NSE (.NS) and BSE (.BO) listed securities
- **Mutual Funds**: Indian mutual fund schemes
- **International**: Global stocks and ETFs through Yahoo Finance

## 🔧 Configuration

### Environment Variables
Create a `.env` file for production deployments:
```env
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
PYTHONUNBUFFERED=1
```

### Streamlit Configuration
Edit `.streamlit/config.toml` for custom settings:
```toml
[server]
port = 8501
enableCORS = false

[theme]
primaryColor = "#0EA5E9"
backgroundColor = "#F0F9FF"
```

## 🔒 Security Features

### User Authentication
- Secure password hashing (SHA-256)
- Session-based authentication
- User data isolation
- Input validation and sanitization

### Data Protection
- SQLite database with proper constraints
- Foreign key relationships for data integrity
- No cross-user data access
- Secure session management

### Deployment Security
- NGINX reverse proxy with SSL termination
- Security headers (XSS, CSRF protection)
- Rate limiting and DDoS protection
- Regular security updates

## 📈 Performance Optimization

### Caching Strategy
- Stock price data cached for 5 minutes
- Database connection pooling
- Efficient query optimization
- Lazy loading of heavy operations

### Scalability
- Stateless application design
- Docker containerization
- Load balancer ready
- Database migration support

## 🛠️ Development

### Project Structure
```
investment-journal/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Multi-container setup
├── nginx.conf           # Reverse proxy configuration
├── .streamlit/
│   └── config.toml      # Streamlit configuration
├── docs/                # Documentation
└── README.md           # This file
```

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black app.py

# Linting
flake8 app.py
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📊 Sample Data

### Test Users
The application starts with a clean database. Create test users through the registration interface.

### Sample Transactions
Example Indian stocks for testing:
- **RELIANCE.NS**: Reliance Industries
- **TCS.NS**: Tata Consultancy Services
- **HDFCBANK.NS**: HDFC Bank
- **INFY.NS**: Infosys Limited

## 🔍 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check database file permissions
ls -la *.db
chmod 644 *.db
```

**Stock Price Fetch Error**
```bash
# Verify internet connection and yfinance
python -c "import yfinance as yf; print(yf.Ticker('RELIANCE.NS').info)"
```

**Port Already in Use**
```bash
# Find and kill process using port 8501
lsof -ti:8501 | xargs kill -9
```

### Performance Issues
- Clear browser cache and cookies
- Check system resources (RAM, CPU)
- Verify database size and optimize queries
- Monitor network latency for stock price fetches

## 📚 Documentation

### API Reference
- [Streamlit Documentation](https://docs.streamlit.io/)
- [yfinance Library](https://pypi.org/project/yfinance/)
- [Plotly Charts](https://plotly.com/python/)

### Additional Resources
- [Investment Analysis Techniques](docs/investment-analysis.md)
- [XIRR Calculation Methods](docs/xirr-calculation.md)
- [Deployment Best Practices](docs/deployment-guide.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

### Getting Help
- Create an issue on GitHub for bugs or feature requests
- Check the documentation for common solutions
- Join our community discussions

### Roadmap
- [ ] PostgreSQL database support
- [ ] Advanced charting and technical indicators
- [ ] Mobile app development
- [ ] Integration with broking APIs
- [ ] Machine learning-based insights
- [ ] Multi-currency support

## 🙏 Acknowledgments

- **Streamlit Team**: For the amazing framework
- **Yahoo Finance**: For providing free stock market data
- **Plotly**: For interactive charting capabilities
- **Community Contributors**: For feedback and improvements

---

**Built with ❤️ for the investment community**

For questions, suggestions, or support, please reach out through GitHub issues or contact the maintainers directly.