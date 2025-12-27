#!/bin/bash
# Setup script for Erle-Brain 2 Autonomous Flight System

echo "=========================================="
echo "Erle-Brain 2 Autonomous Flight Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

echo "✓ Python 3 found"
echo ""

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs
echo "✓ Logs directory created"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
echo "This may take a few minutes..."

pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    echo "Try: sudo pip3 install -r requirements.txt"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit config/flight_params.yaml with your settings"
echo "2. Update mission files with your GPS coordinates"
echo "3. Test connection: python3 src/utils/connection.py"
echo "4. Monitor telemetry: python3 src/telemetry_monitor.py"
echo "5. Run test flight: python3 src/autonomous_flight.py --test"
echo ""
echo "⚠️  IMPORTANT: Always test in simulation first!"
echo "⚠️  Read QUICKSTART.md for detailed instructions"
echo ""
echo "For SITL simulation testing:"
echo "  - Install ArduPilot SITL on your development computer"
echo "  - Use connection string: tcp:127.0.0.1:5760"
echo ""
echo "Happy flying! 🚁"
