# GPS Activity Visualizer

A browser-based application for visualizing multiple TCX (Training Center XML) and GPX (GPS Exchange Format) activity files on a map.

![TCX Visualizer Screenshot](https://img.shields.io/badge/Activity-Visualizer-blue)

## 🌟 Features

- **Multiple File Support**: Upload and visualize multiple TCX and GPX files simultaneously, including a mix of both formats
- **Activity Type Recognition**: Automatically detects and color-codes different activity types:
  - 🏃 Running (Red)
  - 🚴 Cycling (Blue) 
  - 🚶 Walking (Green)
  - 🏊 Swimming (Teal)
  - 💪 Other activities (Purple)
- **Interactive Map**: Pan, zoom, and explore your activities on an OpenStreetMap
- **Drag & Drop**: Drag TCX or GPX files onto the page to upload
- **Activity Management**: Toggle visibility, focus on specific activities, or remove them
- **Statistics Dashboard**: View total distance, time, and activity counts
- **Responsive Design**: Works on desktop and mobile devices
- **No Server Required**: Runs entirely in your browser - your data never leaves your device

## 🚀 Getting Started

### Option 1: Simple Setup (Recommended)

1. Download the files:
   - `index.html`
   - `tcx-visualizer.js`

2. Open `index.html` in any modern web browser

3. Upload your TCX or GPX files by:
   - Dragging and dropping them onto the upload area
   - Or clicking "Browse Files" to select them

### Option 2: Local Development Server

If you prefer to run a local server (recommended for development):

```bash
# Navigate to the web-ui directory
cd web-ui

# Using Python 3
python -m http.server 8080

# Using Node.js (if you have it installed)
npx serve .
```

Then open `http://localhost:8080` in your browser.

## 📁 Supported File Formats

- **TCX files** (`.tcx`) - Training Center XML exported by Garmin and other fitness services
- **GPX files** (`.gpx`) - GPX tracks and routes, including names, activity types, timestamps, elevation, and heart rate extensions
- The application parses:
  - GPS coordinates (latitude/longitude)
  - Activity types (Running, Cycling, Walking, Swimming, etc.)
  - Timestamps and duration
  - Distance and elevation data
  - Heart rate data (if available)

## 🎮 How to Use

1. **Upload Files**: Drag TCX or GPX files onto the upload area or use the browse button
2. **View Activities**: Each activity appears as a colored track on the map with a start marker
3. **Interact with Activities**:
   - Click markers for detailed information
   - Use sidebar controls to toggle visibility
   - Focus on specific activities to zoom to them
   - Remove activities you don't want to see
4. **Explore Statistics**: View aggregated data in the stats panel

## 🔧 Technical Details

### Architecture
- **Frontend Only**: Pure HTML, CSS, and JavaScript - no backend required
- **Activity Parsing**: Local XML parsers handle TCX activities and GPX tracks or routes
- **Mapping**: Uses Leaflet.js for interactive maps
- **Icons**: Font Awesome icons for activity types
- **Styling**: Modern, responsive CSS with a clean interface

### Browser Compatibility
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

### Dependencies (loaded via CDN)
- Leaflet 1.9.4 - Interactive maps
- Font Awesome 6.4.0 - Icons
- Leaflet Awesome Markers 2.0.2 - Custom map markers

## 📊 Data Privacy

Your privacy is important:
- ✅ **All processing happens locally** in your browser
- ✅ **No data is uploaded** to any server
- ✅ **No tracking or analytics**
- ✅ **Works offline** once loaded

## 🔄 Supported Activity Types

The visualizer automatically recognizes these activity types from TCX metadata and GPX track types:

| Activity Type | Color | Icon |
|---------------|-------|------|
| Running | Red (#e74c3c) | 🏃 |
| Cycling/Biking | Blue (#3498db) | 🚴 |
| Walking | Green (#2ecc71) | 🚶 |
| Swimming | Teal (#1abc9c) | 🏊 |
| Other | Purple (#9b59b6) | 💪 |

## 🐛 Troubleshooting

### Files won't upload
- Ensure files have a `.tcx` or `.gpx` extension
- Check that files contain valid XML for the selected format
- Try refreshing the page and uploading again

### Activities don't appear on map
- Verify the activity files contain GPS coordinates
- Some indoor activities may not have location data
- Check browser console for error messages

### Map doesn't load
- Ensure you have an internet connection (for map tiles)
- Try refreshing the page
- Check if browser is blocking JavaScript

## 🎯 Exporting Activity Files

### From Garmin Connect
1. Go to Garmin Connect website
2. Navigate to Activities
3. Select an activity
4. Click the gear icon → Export to TCX

### From Strava
1. Go to your activity page
2. Click the three dots menu
3. Select "Export TCX"

## 🛠 Development

Want to modify or extend the visualizer?

```bash
git clone <repository-url>
cd GarminToStrava/web-ui
# Edit files and test in browser
```

### Key Files
- `index.html` - Main application interface
- `tcx-visualizer.js` - Core application logic
- Styles are embedded in the HTML file

### Adding New Features
The code is modular and well-commented. Key areas for extension:
- `activityColors` and `activityIcons` objects for new activity types
- `parseTCX()` and `parseGPX()` methods for additional data parsing
- `addActivityToMap()` for new visualization features

## 📜 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features  
- Submit pull requests
- Improve documentation

## 🙏 Acknowledgments

- **Leaflet** - Amazing open-source mapping library
- **OpenStreetMap** - Free, editable map of the world
- **Font Awesome** - Beautiful icon library
- **Garmin** - For the TCX file format
- **GPX** - For the open GPS Exchange Format

---

Made with ❤️ for the fitness tracking community 