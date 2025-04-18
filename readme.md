# 8086 Architecture Simulator

## Features:
- Monaco editor for assembly code input
- Step-by-step simulation
- Register & flag tracking
- Downloadable simulation reports (JSON & PDF)
- Session support
- Cloud-ready deployment with Docker

## Setup:
1. Clone this repository
2. Run `pip install -r requirements.txt`
3. Run `python run.py`

## Deploy to Cloud (Render, etc):
1. Build Docker image: `docker build -t 8086-simulator .`
2. Deploy it to Render / Heroku / Railway, etc.