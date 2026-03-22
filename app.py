#!/usr/bin/env python3
"""
Malaysia Stock Dashboard - Backend API
Provides real-time stock data for the web interface.
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import json
import os

# Try to import database cache
try:
    from db_cache import get_quote as db_get_quote, save_quote as db_save_quote, get_history as db_get_history, save_history as db_save_history
    USE_CACHE = True
except:
    USE_CACHE = False

app = Flask(__name__)
CORS(app)

# Malaysia Stocks + Futures
MALAYSIA_STOCKS = {
    # Stocks
    'Maybank': '1155.KL',
    'Public Bank': '1295.KL',
    'CIMB': '1023.KL',
    'Tenaga': '5347.KL',
    'Petronas': '5681.KL',
    'Genting': '3182.KL',
    'Axiata': '6888.KL',
    'Maxis': '6012.KL',
    'Dialog': '7277.KL',
    'Gamuda': '5398.KL',
    'IOI': '4863.KL',
    'KLK': '7038.KL',
    'QL': '7084.KL',
    'RHB': '1066.KL',
    'Hong Leong': '1082.KL',
    'Suntec': '5120.KL',
    'Kepco': '4713.KL',
    'Yinson': '7293.KL',
    'Sapura': '5218.KL',
    # Futures (using common Malaysia futures codes)
    'KLCI Futures (FKLI)': 'FKLI',
    'KLCI Index': '^KLSE',
    # Popular ETFs
    'SABANA REIT': 'SABANA REIT',
    'SUNWAY REIT': 'SUNWAY REIT',
    'KLCCP STAPLED': 'KLCCP STAPLED',
}

# KLCI 30 Constituents - Official FBM KLCI Top 30 (2024-2025)
KLCI_30 = {
    # Financials - Banks (7)
    'Maybank': {'ticker': '1155.KL', 'sector': 'Financials'},
    'Public Bank': {'ticker': '1295.KL', 'sector': 'Financials'},
    'CIMB Group': {'ticker': '1023.KL', 'sector': 'Financials'},
    'RHB Bank': {'ticker': '1066.KL', 'sector': 'Financials'},
    'Hong Leong Bank': {'ticker': '1082.KL', 'sector': 'Financials'},
    'AmBank': {'ticker': '1015.KL', 'sector': 'Financials'},
    'Bank Islam': {'ticker': '5258.KL', 'sector': 'Financials'},
    
    # Energy (3)
    'Petronas D&P': {'ticker': '5681.KL', 'sector': 'Energy'},
    'Petronas Chemicals': {'ticker': '5182.KL', 'sector': 'Energy'},
    'Dialog': {'ticker': '7277.KL', 'sector': 'Energy'},
    
    # Utilities (1)
    'Tenaga': {'ticker': '5347.KL', 'sector': 'Utilities'},
    
    # Telecommunications (3)
    'CelcomDigi': {'ticker': '6947.KL', 'sector': 'Telecommunications'},
    'Maxis': {'ticker': '6012.KL', 'sector': 'Telecommunications'},
    'Telekom Malaysia': {'ticker': '4863.KL', 'sector': 'Telecommunications'},
    
    # Consumer (3)
    'Genting': {'ticker': '3182.KL', 'sector': 'Consumer'},
    'Genting Malaysia': {'ticker': '4715.KL', 'sector': 'Consumer'},
    'Nestle': {'ticker': '4707.KL', 'sector': 'Consumer'},
    
    # Industrial (5)
    'Gamuda': {'ticker': '5398.KL', 'sector': 'Industrial'},
    'Sime Darby': {'ticker': '4197.KL', 'sector': 'Industrial'},
    'Press Metal': {'ticker': '8869.KL', 'sector': 'Industrial'},
    'SP Setia': {'ticker': '5132.KL', 'sector': 'Industrial'},
    'MRCB': {'ticker': '5273.KL', 'sector': 'Industrial'},
    
    # Real Estate (3)
    'KLCCP Group': {'ticker': '4162.KL', 'sector': 'Real Estate'},
    'Sunway': {'ticker': '5211.KL', 'sector': 'Real Estate'},
    'UEM Sunrise': {'ticker': '5243.KL', 'sector': 'Real Estate'},
    
    # Plantation (2)
    'IOI Corp': {'ticker': '4863.KL', 'sector': 'Plantation'},
    'KLK': {'ticker': '7038.KL', 'sector': 'Plantation'},
    
    # Technology (3)
    'Inari': {'ticker': '0166.KL', 'sector': 'Technology'},
    'Unisem': {'ticker': '5566.KL', 'sector': 'Technology'},
    'MPI': {'ticker': '3867.KL', 'sector': 'Technology'},
    
    # Healthcare (2)
    'IHH': {'ticker': '5225.KL', 'sector': 'Healthcare'},
    'KPJ': {'ticker': '5878.KL', 'sector': 'Healthcare'},
}

# Sector definitions for KLCI
KLCI_SECTORS = [
    {'id': 'all', 'name': 'All', 'icon': '📊'},
    {'id': 'Financials', 'name': 'Financials', 'icon': '🏦'},
    {'id': 'Energy', 'name': 'Energy', 'icon': '⚡'},
    {'id': 'Utilities', 'name': 'Utilities', 'icon': '🔌'},
    {'id': 'Telecommunications', 'name': 'Telco', 'icon': '📱'},
    {'id': 'Consumer', 'name': 'Consumer', 'icon': '🛒'},
    {'id': 'Industrial', 'name': 'Industrial', 'icon': '🏭'},
    {'id': 'Real Estate', 'name': 'Properties', 'icon': '🏠'},
    {'id': 'Plantation', 'name': 'Plantation', 'icon': '🌴'},
    {'id': 'Technology', 'name': 'Tech', 'icon': '💻'},
    {'id': 'Healthcare', 'name': 'Healthcare', 'icon': '🏥'},
]

# Serve index.html at root
@app.route('/')
def index():
    return send_file('index.html')

# Remove duplicate - using MALAYSIA_STOCKS from above (with futures)

@app.route('/api/stocks')
def get_stocks():
    """Get list of available stocks"""
    return jsonify(MALAYSIA_STOCKS)

@app.route('/api/quote/<ticker>')
def get_quote(ticker):
    """Get current quote - with caching"""
    # Check cache first
    if USE_CACHE:
        cached = db_get_quote(ticker, max_age_seconds=300)  # 5 min cache
        if cached:
            cached['from_cache'] = True
            return jsonify(cached)
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period='1d', interval='1m')
        
        current_price = float(hist['Close'].iloc[-1]) if not hist.empty else None
        prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
        
        if current_price and prev_close:
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100
        else:
            change = change_pct = 0
        
        result = {
            'ticker': ticker,
            'name': info.get('longName', info.get('shortName', ticker)),
            'price': current_price,
            'prev_close': prev_close,
            'change': change,
            'change_pct': change_pct,
            'volume': info.get('volume'),
            'market_cap': info.get('marketCap'),
            'day_high': info.get('dayHigh'),
            'day_low': info.get('dayLow'),
            'week52_high': info.get('fiftyTwoWeekHigh'),
            'week52_low': info.get('fiftyTwoWeekLow'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to cache
        if USE_CACHE:
            db_save_quote(ticker, result)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/history/<ticker>')
def get_stock_history(ticker):
    """Get historical data for charting - with caching"""
    period = request.args.get('period', '1mo')
    interval = request.args.get('interval', '1d')
    
    # Check cache first (1 hour for history)
    if USE_CACHE:
        cached = db_get_history(ticker, period, interval, max_age_seconds=3600)
        if cached:
            cached['from_cache'] = True
            return jsonify(cached)
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            return jsonify({'error': 'No data available'}), 400
        
        # Format for charting
        data = []
        for idx, row in hist.iterrows():
            data.append({
                'time': idx.isoformat(),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })
        
        result = {
            'ticker': ticker,
            'period': period,
            'interval': interval,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to cache
        if USE_CACHE:
            db_save_history(ticker, period, interval, result)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/intraday/<ticker>')
def get_intraday(ticker):
    """Get intraday data (minute-level)"""
    try:
        stock = yf.Ticker(ticker)
        # Get 1-day intraday with 1-minute intervals
        hist = stock.history(period='1d', interval='1m')
        
        if hist.empty:
            return jsonify({'error': 'No data available'}), 400
        
        data = []
        for idx, row in hist.iterrows():
            data.append({
                'time': idx.strftime('%H:%M'),
                'timestamp': idx.isoformat(),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })
        
        return jsonify({
            'ticker': ticker,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/technicals/<ticker>')
def get_technicals(ticker):
    """Get technical indicators"""
    import pandas as pd
    import numpy as np
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='3mo', interval='1d')
        
        if hist.empty:
            return jsonify({'error': 'No data available'}), 400
        
        close = hist['Close']
        
        # Moving Averages
        ma20 = close.rolling(window=20).mean()
        ma50 = close.rolling(window=50).mean()
        ma200 = close.rolling(window=200).mean()
        
        # EMA
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        
        # MACD
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        
        # Format data
        data = []
        for idx in hist.index:
            date_str = idx.isoformat()
            data.append({
                'time': date_str,
                'close': float(close.loc[idx]),
                'ma20': float(ma20.loc[idx]) if not pd.isna(ma20.loc[idx]) else None,
                'ma50': float(ma50.loc[idx]) if not pd.isna(ma50.loc[idx]) else None,
                'ma200': float(ma200.loc[idx]) if not pd.isna(ma200.loc[idx]) else None,
                'macd': float(macd.loc[idx]) if not pd.isna(macd.loc[idx]) else None,
                'macd_signal': float(signal.loc[idx]) if not pd.isna(signal.loc[idx]) else None,
                'rsi': float(rsi.loc[idx]) if not pd.isna(rsi.loc[idx]) else None,
                'bb_upper': float(bb_upper.loc[idx]) if not pd.isna(bb_upper.loc[idx]) else None,
                'bb_middle': float(bb_middle.loc[idx]) if not pd.isna(bb_middle.loc[idx]) else None,
                'bb_lower': float(bb_lower.loc[idx]) if not pd.isna(bb_lower.loc[idx]) else None,
            })
        
        # Latest values
        latest = data[-1] if data else {}
        
        return jsonify({
            'ticker': ticker,
            'data': data,
            'latest': {
                'rsi': latest.get('rsi'),
                'macd': latest.get('macd'),
                'macd_signal': latest.get('macd_signal'),
                'ma20': latest.get('ma20'),
                'ma50': latest.get('ma50'),
                'ma200': latest.get('ma200'),
                'bb_upper': latest.get('bb_upper'),
                'bb_lower': latest.get('bb_lower'),
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/market overview')
def get_market_overview():
    """Get overview of Malaysia market"""
    try:
        # KLCI Index
        klci = yf.Ticker('^KLSE')
        klci_hist = klci.history(period='1d')
        
        # Top stocks
        top_stocks = ['1155.KL', '1295.KL', '5347.KL', '3182.KL', '1023.KL']
        
        market_data = []
        for ticker in top_stocks:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period='1d')
                
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    prev = info.get('previousClose') or info.get('regularMarketPreviousClose') or price
                    change = ((price - prev) / prev) * 100
                    
                    market_data.append({
                        'ticker': ticker,
                        'name': info.get('shortName', ticker),
                        'price': price,
                        'change_pct': change
                    })
            except:
                continue
        
        return jsonify({
            'klci': {
                'value': float(klci_hist['Close'].iloc[-1]) if not klci_hist.empty else None,
                'change': float(klci_hist['Close'].iloc[-1] - klci_hist['Open'].iloc[-1]) if not klci_hist.empty else None
            },
            'top_stocks': market_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/klci/sectors')
def get_klci_sectors():
    """Get KLCI sectors list"""
    return jsonify(KLCI_SECTORS)

@app.route('/api/klci/constituents')
def get_klci_constituents():
    """Get all KLCI 30 constituents with sector info"""
    sector = request.args.get('sector', 'all')
    
    # Get unique constituents by ticker
    constituents = {}
    for name, info in KLCI_30.items():
        ticker = info['ticker']
        if ticker not in constituents:
            constituents[ticker] = {
                'name': name,
                'ticker': ticker,
                'sector': info['sector'],
                'subsector': info['subsector']
            }
    
    # Filter by sector if needed
    result = []
    for ticker, info in constituents.items():
        if sector == 'all' or info['sector'] == sector:
            result.append(info)
    
    return jsonify({
        'sector': sector,
        'constituents': result,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/klci/quote')
def get_klci_quotes():
    """Get quotes for all KLCI 30 constituents - with file-based cache"""
    import os
    import time
    import threading
    
    sector = request.args.get('sector', 'all')
    cache_file = os.path.join(os.path.dirname(__file__), 'klci_cache.json')
    cache_max_age = 180  # 3 minutes cache
    
    # Simple lock for refresh
    refresh_lock = getattr(get_klci_quotes, 'lock', None)
    if refresh_lock is None:
        refresh_lock = threading.Lock()
        get_klci_quotes.lock = refresh_lock
    
    # Try to load from cache first
    cached_data = None
    if os.path.exists(cache_file):
        try:
            mtime = os.path.getmtime(cache_file)
            if time.time() - mtime < cache_max_age:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
        except:
            pass
    
    if cached_data and 'quotes' in cached_data:
        results = cached_data['quotes']
    else:
        # Need to refresh - acquire lock
        if refresh_lock.acquire(blocking=False):
            try:
                tickers_seen = set()
                stocks_to_fetch = []
                
                for name, info in KLCI_30.items():
                    ticker = info['ticker']
                    if ticker not in tickers_seen:
                        tickers_seen.add(ticker)
                        stocks_to_fetch.append({'name': name, 'ticker': ticker, 'sector': info['sector']})
                
                results = []
                
                for stock in stocks_to_fetch:
                    ticker = stock['ticker']
                    try:
                        stock_obj = yf.Ticker(ticker)
                        # Use 5 day period for more reliable data
                        hist = stock_obj.history(period='5d', timeout=10)
                        
                        if not hist.empty:
                            # Get last trading day's close and current price
                            current_price = float(hist['Close'].iloc[-1])
                            prev_close = float(hist['Open'].iloc[0])
                            change = current_price - prev_close
                            change_pct = (change / prev_close) * 100 if prev_close else 0
                            
                            results.append({
                                'name': stock['name'],
                                'ticker': ticker,
                                'sector': stock['sector'],
                                'price': current_price,
                                'prev_close': prev_close,
                                'change': change,
                                'change_pct': change_pct,
                                'volume': int(hist['Volume'].iloc[-1]) if len(hist) > 0 else 0,
                            })
                    except Exception as e:
                        print(f"Error {ticker}: {e}")
                        continue
                
                # Save to cache
                try:
                    with open(cache_file, 'w') as f:
                        json.dump({'quotes': results, 'timestamp': datetime.now().isoformat()}, f)
                except:
                    pass
            finally:
                refresh_lock.release()
        else:
            # Another thread refreshing - return empty, frontend will retry
            return jsonify({'quotes': [], 'sector_summary': {}, 'refreshing': True, 'timestamp': datetime.now().isoformat()})
    
    if not results:
        return jsonify({'quotes': [], 'sector_summary': {}, 'timestamp': datetime.now().isoformat()})
    
    # Filter by sector
    if sector != 'all':
        results = [r for r in results if r['sector'] == sector]
    
    results.sort(key=lambda x: (x['sector'], x.get('change_pct', 0)))
    
    # Calculate sector summary from ALL data
    all_results = cached_data.get('quotes', results) if cached_data else results
    sector_summary = {}
    for r in all_results:
        sect = r['sector']
        if sect not in sector_summary:
            sector_summary[sect] = {'up': 0, 'down': 0, 'total': 0, 'avg_change': 0}
        sector_summary[sect]['total'] += 1
        if r.get('change_pct', 0) > 0:
            sector_summary[sect]['up'] += 1
        elif r.get('change_pct', 0) < 0:
            sector_summary[sect]['down'] += 1
    
    for sect in sector_summary:
        stocks_in_sect = [r for r in all_results if r['sector'] == sect]
        if stocks_in_sect:
            sector_summary[sect]['avg_change'] = sum(r.get('change_pct', 0) for r in stocks_in_sect) / len(stocks_in_sect)
    
    return jsonify({
        'quotes': results,
        'sector_summary': sector_summary,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/klci/index')
def get_klci_index():
    """Get KLCI Index with constituent breakdown"""
    try:
        klci = yf.Ticker('^KLSE')
        klci_hist = klci.history(period='1d')
        
        if not klci_hist.empty:
            current = float(klci_hist['Close'].iloc[-1])
            prev = float(klci_hist['Open'].iloc[-1])
            change = current - prev
            change_pct = (change / prev) * 100 if prev else 0
        else:
            current = prev = change = change_pct = None
        
        # Get major indices
        indices = []
        major_tickers = ['^KLSE', 'FKLI']
        for ticker in major_tickers:
            try:
                idx = yf.Ticker(ticker)
                h = idx.history(period='1d')
                if not h.empty:
                    c = float(h['Close'].iloc[-1])
                    o = float(h['Open'].iloc[-1])
                    ch = c - o
                    ch_pct = (ch / o) * 100 if o else 0
                    indices.append({
                        'ticker': ticker,
                        'name': 'KLCI' if ticker == '^KLSE' else 'KLCI Futures',
                        'price': c,
                        'change': ch,
                        'change_pct': ch_pct
                    })
            except:
                continue
        
        return jsonify({
            'klci': {
                'value': current,
                'prev_close': prev,
                'change': change,
                'change_pct': change_pct
            },
            'indices': indices,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ========== WATCHLIST API ==========
WATCHLIST_FILE = os.path.join(os.path.dirname(__file__), 'watchlist.json')
ALERTS_FILE = os.path.join(os.path.dirname(__file__), 'alerts.json')

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            pass
    return default

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/api/watchlist')
def get_watchlist():
    """Get user's watchlist"""
    watchlist = load_json(WATCHLIST_FILE, [])
    return jsonify({'watchlist': watchlist, 'timestamp': datetime.now().isoformat()})

@app.route('/api/watchlist/add', methods=['POST'])
def add_to_watchlist():
    """Add stock to watchlist"""
    data = request.get_json()
    ticker = data.get('ticker', '').upper()
    name = data.get('name', ticker)
    
    if not ticker:
        return jsonify({'error': 'Ticker required'}), 400
    
    watchlist = load_json(WATCHLIST_FILE, [])
    
    # Check if already exists
    if not any(s.get('ticker') == ticker for s in watchlist):
        watchlist.append({'ticker': ticker, 'name': name, 'added_at': datetime.now().isoformat()})
        save_json(WATCHLIST_FILE, watchlist)
    
    return jsonify({'success': True, 'watchlist': watchlist})

@app.route('/api/watchlist/remove', methods=['POST'])
def remove_from_watchlist():
    """Remove stock from watchlist"""
    data = request.get_json()
    ticker = data.get('ticker', '').upper()
    
    watchlist = load_json(WATCHLIST_FILE, [])
    watchlist = [s for s in watchlist if s.get('ticker') != ticker]
    save_json(WATCHLIST_FILE, watchlist)
    
    return jsonify({'success': True, 'watchlist': watchlist})

# ========== ALERTS API ==========
@app.route('/api/alerts')
def get_alerts():
    """Get all alerts"""
    alerts = load_json(ALERTS_FILE, [])
    return jsonify({'alerts': alerts, 'timestamp': datetime.now().isoformat()})

@app.route('/api/alerts/add', methods=['POST'])
def add_alert():
    """Add new alert"""
    data = request.get_json()
    ticker = data.get('ticker', '').upper()
    alert_type = data.get('type', 'price')  # price, rsi, macd
    condition = data.get('condition', 'above')  # above, below, crossover, crossunder
    value = float(data.get('value', 0))
    name = data.get('name', ticker)
    
    if not ticker:
        return jsonify({'error': 'Ticker required'}), 400
    
    alerts = load_json(ALERTS_FILE, [])
    
    # Generate unique ID
    import uuid
    alert_id = str(uuid.uuid4())[:8]
    
    new_alert = {
        'id': alert_id,
        'ticker': ticker,
        'name': name,
        'type': alert_type,
        'condition': condition,
        'value': value,
        'created_at': datetime.now().isoformat(),
        'triggered': False,
        'triggered_at': None
    }
    
    alerts.append(new_alert)
    save_json(ALERTS_FILE, alerts)
    
    return jsonify({'success': True, 'alert': new_alert, 'alerts': alerts})

@app.route('/api/alerts/remove', methods=['POST'])
def remove_alert():
    """Remove alert by ID"""
    data = request.get_json()
    alert_id = data.get('id')
    
    alerts = load_json(ALERTS_FILE, [])
    alerts = [a for a in alerts if a.get('id') != alert_id]
    save_json(ALERTS_FILE, alerts)
    
    return jsonify({'success': True, 'alerts': alerts})

@app.route('/api/alerts/check')
def check_alerts():
    """Check all alerts against current data"""
    alerts = load_json(ALERTS_FILE, [])
    triggered = []
    
    for alert in alerts:
        if alert.get('triggered'):
            continue
            
        try:
            ticker = alert['ticker']
            alert_type = alert['type']
            condition = alert['condition']
            target_value = alert['value']
            
            stock = yf.Ticker(ticker)
            
            if alert_type == 'price':
                hist = stock.history(period='1d', interval='1m')
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    
                    if condition == 'above' and current_price > target_value:
                        alert['triggered'] = True
                        alert['triggered_at'] = datetime.now().isoformat()
                        alert['current_value'] = current_price
                        triggered.append(alert)
                    elif condition == 'below' and current_price < target_value:
                        alert['triggered'] = True
                        alert['triggered_at'] = datetime.now().isoformat()
                        alert['current_value'] = current_price
                        triggered.append(alert)
                        
            elif alert_type in ['rsi', 'macd', 'macd_signal']:
                hist = stock.history(period='3mo', interval='1d')
                if not hist.empty:
                    close = hist['Close']
                    
                    if alert_type == 'rsi':
                        delta = close.diff()
                        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        rsi = 100 - (100 / (1 + rs))
                        current = float(rsi.iloc[-1])
                        
                        if condition == 'above' and current > target_value:
                            alert['triggered'] = True
                            alert['triggered_at'] = datetime.now().isoformat()
                            alert['current_value'] = current
                            triggered.append(alert)
                        elif condition == 'below' and current < target_value:
                            alert['triggered'] = True
                            alert['triggered_at'] = datetime.now().isoformat()
                            alert['current_value'] = current
                            triggered.append(alert)
                            
                    elif alert_type in ['macd', 'macd_signal']:
                        ema12 = close.ewm(span=12, adjust=False).mean()
                        ema26 = close.ewm(span=26, adjust=False).mean()
                        macd = ema12 - ema26
                        signal = macd.ewm(span=9, adjust=False).mean()
                        macd_val = float(macd.iloc[-1])
                        signal_val = float(signal.iloc[-1])
                        
                        if alert_type == 'macd':
                            current = macd_val
                        else:
                            current = signal_val
                            
                        if condition == 'above' and current > target_value:
                            alert['triggered'] = True
                            alert['triggered_at'] = datetime.now().isoformat()
                            alert['current_value'] = current
                            triggered.append(alert)
                        elif condition == 'below' and current < target_value:
                            alert['triggered'] = True
                            alert['triggered_at'] = datetime.now().isoformat()
                            alert['current_value'] = current
                            triggered.append(alert)
                        elif condition == 'crossover' and macd_val > signal_val and alert.get('_last_macd', 0) <= alert.get('_last_signal', 0):
                            alert['triggered'] = True
                            alert['triggered_at'] = datetime.now().isoformat()
                            alert['current_value'] = macd_val
                            triggered.append(alert)
                        elif condition == 'crossunder' and macd_val < signal_val and alert.get('_last_macd', 0) >= alert.get('_last_signal', 0):
                            alert['triggered'] = True
                            alert['triggered_at'] = datetime.now().isoformat()
                            alert['current_value'] = macd_val
                            triggered.append(alert)
        except Exception as e:
            print(f"Error checking alert {alert.get('id')}: {e}")
            continue
    
    # Save updated alerts
    save_json(ALERTS_FILE, alerts)
    
    return jsonify({
        'triggered': triggered,
        'total_alerts': len(alerts),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/alerts/reset', methods=['POST'])
def reset_alert():
    """Reset a triggered alert"""
    data = request.get_json()
    alert_id = data.get('id')
    
    alerts = load_json(ALERTS_FILE, [])
    for alert in alerts:
        if alert.get('id') == alert_id:
            alert['triggered'] = False
            alert['triggered_at'] = None
            alert.pop('current_value', None)
            break
    
    save_json(ALERTS_FILE, alerts)
    return jsonify({'success': True, 'alerts': alerts})

# ========== METHODOLOGY RULES API ==========
METHODOLOGY_RULES = {
    'golden_cross': {
        'name': 'Golden Cross',
        'description': 'MA50 crosses above MA200 - Bullish signal',
        'indicator': 'ma50_ma200',
        'type': 'crossover'
    },
    'death_cross': {
        'name': 'Death Cross', 
        'description': 'MA50 crosses below MA200 - Bearish signal',
        'indicator': 'ma50_ma200',
        'type': 'crossunder'
    },
    'rsi_oversold': {
        'name': 'RSI Oversold',
        'description': 'RSI below 30 - Potential buy opportunity',
        'indicator': 'rsi',
        'threshold': 30,
        'condition': 'below'
    },
    'rsi_overbought': {
        'name': 'RSI Overbought',
        'description': 'RSI above 70 - Potential sell signal',
        'indicator': 'rsi',
        'threshold': 70,
        'condition': 'above'
    },
    'macd_bullish': {
        'name': 'MACD Bullish Crossover',
        'description': 'MACD crosses above signal line',
        'indicator': 'macd',
        'type': 'crossover'
    },
    'macd_bearish': {
        'name': 'MACD Bearish Crossover',
        'description': 'MACD crosses below signal line',
        'indicator': 'macd',
        'type': 'crossunder'
    },
    'bb_support': {
        'name': 'Bollinger Bands Support',
        'description': 'Price touches lower Bollinger Band',
        'indicator': 'bb_lower',
        'type': 'touch'
    },
    'bb_resistance': {
        'name': 'Bollinger Bands Resistance',
        'description': 'Price touches upper Bollinger Band',
        'indicator': 'bb_upper',
        'type': 'touch'
    },
    'price_above_ma50': {
        'name': 'Price Above MA50',
        'description': 'Current price above 50-day MA',
        'indicator': 'price_ma50',
        'condition': 'above'
    },
    'price_below_ma50': {
        'name': 'Price Below MA50',
        'description': 'Current price below 50-day MA',
        'indicator': 'price_ma50',
        'condition': 'below'
    }
}

@app.route('/api/methodology')
def get_methodology_rules():
    """Get available methodology/analysis rules"""
    return jsonify({
        'rules': METHODOLOGY_RULES,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/methodology/analyze/<ticker>')
def analyze_with_methodology(ticker):
    """Analyze stock with all methodology rules"""
    import pandas as pd
    import numpy as np
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='6mo', interval='1d')
        
        if hist.empty:
            return jsonify({'error': 'No data available'}), 400
        
        close = hist['Close']
        
        # Calculate indicators
        ma20 = close.rolling(window=20).mean()
        ma50 = close.rolling(window=50).mean()
        ma200 = close.rolling(window=200).mean()
        
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        
        current_price = float(close.iloc[-1])
        
        # Apply methodology rules
        results = {}
        
        # Golden/Death Cross
        if len(ma50) > 1 and len(ma200) > 1:
            ma50_prev = float(ma50.iloc[-2])
            ma200_prev = float(ma200.iloc[-2])
            ma50_curr = float(ma50.iloc[-1])
            ma200_curr = float(ma200.iloc[-1])
            
            results['golden_cross'] = ma50_curr > ma200_curr and ma50_prev <= ma200_prev
            results['death_cross'] = ma50_curr < ma200_curr and ma50_prev >= ma200_prev
        
        # RSI
        rsi_val = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        results['rsi_oversold'] = rsi_val < 30 if rsi_val else False
        results['rsi_overbought'] = rsi_val > 70 if rsi_val else False
        results['rsi_value'] = rsi_val
        
        # MACD
        macd_val = float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None
        signal_val = float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else None
        
        if len(macd) > 1 and len(signal) > 1:
            macd_prev = float(macd.iloc[-2])
            signal_prev = float(signal.iloc[-2])
            
            results['macd_bullish'] = macd_val > signal_val and macd_prev <= signal_prev
            results['macd_bearish'] = macd_val < signal_val and macd_prev >= signal_prev
        
        results['macd_value'] = macd_val
        results['macd_signal_value'] = signal_val
        
        # Bollinger Bands
        bb_upper_val = float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None
        bb_lower_val = float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None
        
        results['bb_support'] = current_price <= bb_lower_val * 1.02 if bb_lower_val else False
        results['bb_resistance'] = current_price >= bb_upper_val * 0.98 if bb_upper_val else False
        
        # Price vs MA
        ma50_val = float(ma50.iloc[-1]) if not pd.isna(ma50.iloc[-1]) else None
        results['price_above_ma50'] = current_price > ma50_val if ma50_val else False
        results['price_below_ma50'] = current_price < ma50_val if ma50_val else False
        
        # Summary
        bullish_signals = sum([
            results.get('golden_cross', False),
            results.get('rsi_oversold', False),
            results.get('macd_bullish', False),
            results.get('bb_support', False),
            results.get('price_above_ma50', False)
        ])
        
        bearish_signals = sum([
            results.get('death_cross', False),
            results.get('rsi_overbought', False),
            results.get('macd_bearish', False),
            results.get('bb_resistance', False),
            results.get('price_below_ma50', False)
        ])
        
        return jsonify({
            'ticker': ticker,
            'current_price': current_price,
            'analysis': results,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'summary': 'BULLISH' if bullish_signals > bearish_signals else 'BEARISH' if bearish_signals > bullish_signals else 'NEUTRAL',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    import sys
    
    # Get host from command line or default to all interfaces
    host = '0.0.0.0'
    port = 8888
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    print("Starting Malaysia Stock Dashboard API...")
    print("Server running at: http://{}:{}".format(host, port))
    app.run(debug=False, host=host, port=port, threaded=True)
