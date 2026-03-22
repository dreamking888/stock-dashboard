const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const path = require('path');

const app = express();
const PORT = 8080;

app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

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

const PY = 'C:\\Users\\david\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';

function runPy(args) {
    return new Promise((resolve, reject) => {
        exec(`${PY} ${__dirname}\\fetch_stock.py ${args.join(' ')}`, { timeout: 30000 }, (err, stdout, stderr) => {
            if (err) reject(err);
            else resolve(stdout);
        });
    });
}

app.get('/api/stocks', (req, res) => res.json(MALAYSIA_STOCKS));

app.get('/api/quote/:ticker', async (req, res) => {
    try {
        const output = await runPy([req.params.ticker]);
        res.json(JSON.parse(output));
    } catch (e) {
        res.status(400).json({ error: e.message });
    }
});

app.get('/api/history/:ticker', async (req, res) => {
    const { ticker } = req.params;
    const period = req.query.period || '1mo';
    const interval = req.query.interval || '1d';
    try {
        const output = await runPy([ticker, period, interval]);
        res.json(JSON.parse(output));
    } catch (e) {
        res.status(400).json({ error: e.message });
    }
});

app.get('/api/technicals/:ticker', async (req, res) => {
    try {
        const output = await runPy([req.params.ticker]);
        res.json(JSON.parse(output));
    } catch (e) {
        res.status(400).json({ error: e.message });
    }
});

app.get('/api/market', async (req, res) => {
    try {
        res.json({
            klci: { value: 1600, change: 5 },
            top_stocks: [],
            timestamp: new Date().toISOString()
        });
    } catch (e) {
        res.status(400).json({ error: e.message });
    }
});

app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'index.html')));

app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Dashboard: http://localhost:${PORT}`);
    console.log(`📍 Network: http://192.168.250.208:${PORT}`);
});
