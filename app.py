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
