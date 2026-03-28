@echo off
cd /d D:\personal\stock_dashboard
echo Starting Flask server...
python app.py > flask_server.log 2>&1
echo Server started on http://0.0.0.0:8888
