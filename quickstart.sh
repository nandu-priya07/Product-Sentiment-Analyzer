#!/bin/bash
# Product Sentiment Analyzer - Quick Start Script
# Run this script to setup and start the application

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Product Sentiment Analyzer - Quick Start                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python installation
echo "✓ Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
python_version=$(python3 --version)
echo "  Found: $python_version"
echo ""

# Create virtual environment
echo "✓ Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Virtual environment created"
else
    echo "  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate
echo "  Activated"
echo ""

# Install dependencies
echo "✓ Installing dependencies..."
pip install -r requirements.txt -q
echo "  Dependencies installed"
echo ""

# Check .env file
echo "✓ Checking configuration..."
if [ ! -f ".env" ]; then
    echo "  WARNING: .env file not found!"
    echo "  Please create .env with MongoDB URI:"
    echo ""
    echo "  MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
    echo "  MONGO_DB_NAME=product_sentiment"
    echo ""
    read -p "  Have you configured .env? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "  .env file found ✓"
fi
echo ""

# Check required directories
echo "✓ Setting up directories..."
mkdir -p exports
mkdir -p data
mkdir -p templates
mkdir -p static/css
mkdir -p static/js
echo "  Directories ready"
echo ""

# Display startup info
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Ready to start!                                           ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Run: python app.py                                        ║"
echo "║  Then: Open http://localhost:5000                          ║"
echo "║                                                            ║"
echo "║  Features:                                                 ║"
echo "║  • Scrape reviews from Amazon & Flipkart                   ║"
echo "║  • Analyze sentiment with AI                               ║"
echo "║  • View interactive dashboards                             ║"
echo "║  • Export data as CSV/JSON                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Ask to start
read -p "Start the application now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting application..."
    python app.py
else
    echo "To start manually, run: python app.py"
fi
