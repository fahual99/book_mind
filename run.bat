@echo off

start cmd /k "cd /d C:\Users\fahaa\OneDrive\Desktop\book_webapp\frontend && npm run dev"

start cmd /k "cd /d C:\Users\fahaa\OneDrive\Desktop\book_webapp\backend && python -m uvicorn app.main:app --reload --port 8000"

start cmd /k "ngrok && ngrok http 3000"