Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d D:\personal\stock_dashboard && python app.py", 0, False
