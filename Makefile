.PHONY: help ui sync install clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make ui       - Start web UI server and open in browser"
	@echo "  make sync     - Run Garmin to Strava sync"
	@echo "  make install  - Install Python dependencies"
	@echo "  make clean    - Clean downloaded files"
	@echo "  make help     - Show this help message"

# Start web UI server
ui:
	@echo "Starting web UI server..."
	@echo "Opening http://localhost:8080 in your browser..."
	@cd web-ui && python -m http.server 8080 &
	@sleep 2
	@open http://localhost:8080 2>/dev/null || echo "Please open http://localhost:8080 in your browser"
	@echo "Press Ctrl+C to stop the server"

# Run Garmin to Strava sync
sync:
	@echo "Running Garmin to Strava sync..."
	uv run garmin2strava.py

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	uv sync

# Clean downloaded files
clean:
	@echo "Cleaning downloads directory..."
	@rm -rf downloads/*.tcx
	@echo "Downloaded TCX files removed"

# Stop any running web servers (cleanup)
stop:
	@echo "Stopping any running Python HTTP servers..."
	@pkill -f "python -m http.server" 2>/dev/null || echo "No servers to stop" 