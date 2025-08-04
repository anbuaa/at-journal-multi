# Investment Journal Git Package

This repository contains all the files needed to deploy the Personal Investment Journal application with multi-user authentication and XIRR calculations.

## 📁 Package Contents

### Core Application Files
- **`app.py`** - Main Streamlit application with multi-user support
- **`requirements.txt`** - Python dependencies
- **`config.toml`** - Streamlit configuration

### Deployment Files
- **`Dockerfile`** - Container configuration for Docker deployment
- **`docker-compose.yml`** - Multi-container setup with NGINX
- **`nginx.conf`** - Reverse proxy configuration
- **`deploy.sh`** - Production deployment script for Ubuntu servers

### Documentation
- **`README.md`** - Comprehensive documentation and setup guide

## 🚀 Quick Start Options

### Option 1: Local Development
```bash
git clone <your-repo-url>
cd investment-journal
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Option 2: Docker Deployment
```bash
git clone <your-repo-url>
cd investment-journal
docker build -t investment-journal .
docker run -p 8501:8501 investment-journal
```

### Option 3: Production VPS Deployment
```bash
git clone <your-repo-url>
cd investment-journal
chmod +x deploy.sh
./deploy.sh your-domain.com your-email@example.com
```

### Option 4: Streamlit Community Cloud
1. Fork this repository to your GitHub account
2. Visit https://share.streamlit.io/
3. Connect your GitHub repository
4. Set main file path as `app.py`
5. Deploy

## 🏗️ Architecture

### Application Features
- **Multi-user authentication** with secure login/registration
- **Multi-portfolio management** for different investment strategies
- **Real-time stock price updates** using Yahoo Finance API
- **Advanced XIRR calculations** for individual securities and portfolios
- **Performance benchmarking** against market indices (NIFTY 50, etc.)
- **Interactive dashboards** with Plotly visualizations
- **Data export functionality** for CSV downloads
- **Sky blue theme** with professional UI/UX

### Technology Stack
- **Frontend**: Streamlit with custom CSS
- **Backend**: Python 3.9+ with SQLite database
- **Authentication**: SHA-256 password hashing
- **Data Source**: Yahoo Finance (yfinance)
- **Visualization**: Plotly Express
- **Deployment**: Docker, NGINX, PM2

## 📊 Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    created_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT 1
);

-- Portfolios table
CREATE TABLE portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Transactions table
CREATE TABLE transactions (
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
);
```

## 🔐 Security Features

### User Authentication
- Secure password hashing using SHA-256
- Session-based authentication
- Complete user data isolation
- Input validation and sanitization

### Production Security
- NGINX reverse proxy with SSL termination
- Security headers (XSS, CSRF protection)
- Rate limiting and DDoS protection
- Fail2ban intrusion prevention
- Regular automated backups

## 🎯 Usage Guide

### Getting Started
1. **Register Account**: Create new user with username, email, password
2. **Create Portfolio**: Set up investment portfolios (e.g., "Growth", "Dividend")
3. **Add Transactions**: Record buy/sell transactions with actual prices
4. **Monitor Performance**: Track real-time portfolio performance and XIRR

### Supported Markets
- **Indian Stocks**: NSE (.NS) and BSE (.BO) listed securities
- **Mutual Funds**: Indian mutual fund schemes
- **International**: Global stocks and ETFs through Yahoo Finance

### Example Stock Symbols
- `RELIANCE.NS` - Reliance Industries (NSE)
- `TCS.NS` - Tata Consultancy Services (NSE)
- `HDFCBANK.NS` - HDFC Bank (NSE)
- `INFY.NS` - Infosys Limited (NSE)

## 🛠️ Deployment Options

### 1. Streamlit Community Cloud (Free)
**Pros**: Free, zero setup, automatic deployments
**Cons**: Public, resource limits, 1 private app limit
**Best for**: Demos, testing, personal use

### 2. VPS Deployment (Recommended)
**Cost**: $5-25/month
**Pros**: Full control, custom domain, SSL, scalable
**Best for**: Production use, multiple users

**Providers**:
- Hetzner: €4-20/month, excellent performance
- DigitalOcean: $5-40/month, beginner-friendly
- Linode: $5-40/month, reliable
- AWS EC2: Pay-as-you-go, enterprise features

### 3. Docker Containers
**Pros**: Consistent deployment, easy scaling
**Best for**: DevOps teams, containerized infrastructure

### 4. Cloud Platforms
- **AWS**: Enterprise-grade with advanced features
- **Azure**: Microsoft ecosystem integration
- **Google Cloud**: AI/ML integration capabilities

## 📈 Performance & Monitoring

### Caching Strategy
- Stock price data cached for 5 minutes
- Database connection optimization
- Lazy loading for heavy operations

### Monitoring Tools
```bash
# Check application status
pm2 status

# View logs
pm2 logs investment-journal

# Monitor system resources
htop

# Check application health
curl http://localhost:8501/_stcore/health
```

### Backup Strategy
- Daily automated database backups
- Application code backups
- 7-day retention policy
- Easy restore procedures

## 🔧 Customization

### Theme Customization
Edit `config.toml` to change colors:
```toml
[theme]
primaryColor = "#0EA5E9"  # Sky blue
backgroundColor = "#F0F9FF"
secondaryBackgroundColor = "#E0F2FE"
textColor = "#1F2937"
```

### Adding New Features
The modular architecture makes it easy to add:
- Additional data sources
- New chart types
- Advanced analytics
- Third-party integrations

## 📚 Support & Documentation

### Getting Help
- Create GitHub issues for bugs/features
- Check README.md for detailed setup
- Review deployment guide for production

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 🎯 Roadmap

### Planned Features
- [ ] PostgreSQL database support
- [ ] Advanced technical indicators
- [ ] Mobile app development
- [ ] Broker API integrations
- [ ] Machine learning insights
- [ ] Multi-currency support

### Performance Improvements
- [ ] Redis caching layer
- [ ] Load balancer support
- [ ] Database query optimization
- [ ] CDN integration

## 📄 License

MIT License - See LICENSE file for details

## 🏆 Features Summary

✅ **Multi-user authentication**
✅ **Multi-portfolio management**
✅ **Real-time stock prices**
✅ **XIRR calculations**
✅ **Performance benchmarking**
✅ **Interactive dashboards**
✅ **Data export**
✅ **Docker deployment**
✅ **Production scripts**
✅ **Security features**
✅ **Comprehensive documentation**

---

**Ready to deploy your personal investment journal with enterprise-grade features!**

For questions or support, create an issue or contact the maintainers.