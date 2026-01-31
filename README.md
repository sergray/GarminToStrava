# Garmin to Strava Tools

A collection of tools for working with Garmin activity data, including a command-line sync tool and a web-based TCX visualizer.

## 🛠 Tools Included

### 1. Python CLI Tool - Garmin to Strava Sync

A command-line tool that automatically syncs latest Garmin activity to Strava.

#### Setup

1. [Install `uv`](https://docs.astral.sh/uv/getting-started/installation/)

2. Install the required dependencies:
```bash
uv sync
```

3. Create a `.env` file based on `.env.example` and fill in credentials:
   - Garmin Connect credentials (email and password)
   - Strava API credentials (you can get these from [Strava API Settings](https://www.strava.com/settings/api))

#### Strava API Setup

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create a new application
3. Set the "Authorization Callback Domain" to `localhost`
4. Copy the Client ID and Client Secret to your `.env` file
5. Run `uv run auth_strava.py`

#### Usage

Run the sync command:
```bash
uv run g2s
```

The tool will:
1. Connect to Garmin account
2. Download latest activity
3. Upload it to Strava
4. Automatically handle token refresh when needed

### 2. Web UI - TCX Activity Visualizer

A beautiful, interactive web application for visualizing multiple TCX activity files on a map with distinctive colors and icons for each activity type.

![TCX Visualizer](https://img.shields.io/badge/Web-Visualizer-blue)

#### Features
- 🗺️ **Interactive Map**: Visualize activities on OpenStreetMap
- 📁 **Multiple Files**: Upload and display multiple TCX files simultaneously
- 🎨 **Activity Types**: Color-coded activities (Running, Cycling, Walking, Swimming)
- 🔒 **Privacy First**: All processing happens locally in your browser
- 📱 **Responsive**: Works on desktop and mobile devices

#### Quick Start

```bash
# Navigate to the web UI directory
cd web-ui

# Start a local server
python -m http.server 8080

# Open in browser
open http://localhost:8080
```

Then drag and drop your TCX files from the `downloads/` folder onto the web page!

📖 **[Full Web UI Documentation →](web-ui/README.md)**

## 📁 Project Structure

```
GarminToStrava/
├── 📄 README.md                    # This file
├── 🐍 garmin2strava.py            # Python CLI sync tool
├── 🔐 auth_strava.py              # Strava authentication
├── 📦 pyproject.toml               # Python dependencies
├── 📂 downloads/                   # Downloaded TCX files
│   ├── 2025-07-26_Running_*.tcx
│   ├── 2025-07-26_Cycling_*.tcx
│   └── ...
└── 📂 web-ui/                     # Web-based TCX visualizer
    ├── 🌐 index.html              # Web application
    ├── ⚡ tcx-visualizer.js       # JavaScript application
    └── 📖 README.md               # Web UI documentationÌ
```

## 🚀 Getting Started

### For Strava Sync (Python CLI)
1. Clone the repository
2. Set up Python environment with `uv sync`
3. Configure Strava API credentials
4. Run `uv run garmin2strava.py`

### For Activity Visualization (Web UI)
1. Navigate to `web-ui/` directory
2. Open `index.html` in a browser OR start a local server
3. Upload your TCX files and explore!

## 🎯 Use Cases

- **Daily Sync**: Use the Python CLI tool to automatically sync new activities to Strava
- **Activity Analysis**: Use the web UI to visualize and compare multiple activities on a map
- **Data Export**: Download activities from Garmin Connect in TCX format
- **Batch Processing**: Sync multiple activities at once

## 📊 Activity Types Supported

Both tools support these activity types:
- 🏃 **Running** 
- 🚴 **Cycling/Biking**
- 🚶 **Walking**
- 🏊 **Swimming** (including Open Water)
- 💪 **Other activities**

## 🔧 Development

This project uses:
- **Python 3.12+** for CLI tools
- **uv** for dependency management
- **Vanilla JavaScript** for web UI
- **Leaflet.js** for interactive mapping
- **Garmin Connect API** for activity downloads
- **Strava API** for activity uploads

## 📜 License

MIT License - see LICENSE.txt for details

## 🤝 Contributing

Contributions welcome! Whether it's:
- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🧪 Testing enhancements

## 🙏 Acknowledgments

- **Garmin** - For the TCX file format
- **Strava** - For the upload API
- **Leaflet** - For the amazing mapping library
- **OpenStreetMap** - For free, open map data
