const express = require('express');
const cors = require('cors');
const yfinance = require('yfinance-api'); // We'll use a different approach
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 6000;

app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

// Malaysia stocks
const MALAYSIA_STOCKS = {
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
    'KLCI Index': '^KLSE'
};

// Helper to run Python script
function runPy(script, args) {
    return new Promise((resolve, reject) => {
        const py = 'C:\\Users\\david\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
        const scriptPath = path.join(__dirname, 'py', script);
        exec(`${py} ${scriptPath} ${args.join(' ')}`, { timeout: 30000 }, (err, stdout, stderr) => {
            if (err) reject(err);
            else resolve(stdout);
        });
    });
}

app.get('/api/stocks', (req, res) => {
    res.json(MALAYSIA_STOCKS);
});

app.get('/api/quote/:ticker', async (req, res) => {
    try {
        const output = await runPy('fetch_stock.py', [req.params.ticker]);
        res.json(JSON.parse(output));
    } catch (e) {
        res.status(400).json({ error: e.message });
    }
});

app.get('/api/history', async (req, res) => {
    const { ticker, period, interval } = req.query;
    try {
        const output = await runPy('history.py', [ticker, period || '1mo', interval || '1d']);
        res.json(JSON.parse(output));
    } catch (e) {
        res.status(400).json({ error: e.message });
    }
});

app.get('/api/technicals/:ticker', async (req, res) => {
    try {
        const output = await runPy('analyze_technical.py', [req.params.ticker]);
        res.json(JSON.parse(output));
    } catch (e) {
        res.status(400).json({ error: e.message });
    }
});

// Root - serve HTML
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Stock Dashboard running at: http://0.0.0.0:${PORT}`);
    console.log(`📍 Access at: http://192.168.250.208:${PORT}`);
});
