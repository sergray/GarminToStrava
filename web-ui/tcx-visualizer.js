/**
 * GPS Activity Visualizer
 * A web application for visualizing multiple TCX and GPX activity files
 */

class TCXVisualizer {
    constructor() {
        this.map = null;
        this.activities = new Map();
        this.activityLayers = new Map();
        this.bounds = null;
        this.activityColors = {
            'Running': '#e74c3c',
            'Cycling': '#3498db', 
            'Biking': '#3498db',
            'Walking': '#2ecc71',
            'Swimming': '#1abc9c',
            'Open Water Swimming': '#1abc9c',
            'Other': '#9b59b6'
        };
        this.activityIcons = {
            'Running': 'fa-running',
            'Cycling': 'fa-bicycle',
            'Biking': 'fa-bicycle', 
            'Walking': 'fa-walking',
            'Swimming': 'fa-swimmer',
            'Open Water Swimming': 'fa-swimmer',
            'Other': 'fa-dumbbell'
        };
        
        this.init();
    }

    init() {
        this.initMap();
        this.setupEventListeners();
        this.initXMLParser();
    }

    initMap() {
        // Initialize Leaflet map
        this.map = L.map('map').setView([52.52, 13.405], 10);

        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(this.map);

        // Initialize bounds
        this.bounds = L.latLngBounds();
    }

    initXMLParser() {
        // Configure fast-xml-parser options for TCX parsing
        this.parserOptions = {
            ignoreAttributes: false,
            attributeNamePrefix: '@_',
            parseAttributeValue: true,
            parseTrueNumberOnly: false,
            trimValues: true
        };
        
        // Check if fast-xml-parser is available
        this.hasXMLParserLibrary = typeof XMLParser !== 'undefined' && window.fxp;
    }

    setupEventListeners() {
        const uploadBox = document.getElementById('uploadBox');
        const fileInput = document.getElementById('fileInput');

        // File input change event
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });

        // Global drag and drop prevention to stop browser from navigating/downloading files
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        document.addEventListener('drop', (e) => {
            e.preventDefault();
        });

        // Prevent drag events on the entire window
        window.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        window.addEventListener('drop', (e) => {
            e.preventDefault();
        });

        // Upload box specific drag and drop events
        uploadBox.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation(); // Stop the event from bubbling up
            uploadBox.classList.add('dragover');
        });

        uploadBox.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadBox.classList.remove('dragover');
        });

        uploadBox.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation(); // Stop the event from bubbling up
            uploadBox.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        });

        // Click to upload
        uploadBox.addEventListener('click', () => {
            fileInput.click();
        });
    }

    async handleFiles(files) {
        const activityFiles = Array.from(files).filter(file =>
            /\.(tcx|gpx)$/i.test(file.name)
        );

        if (activityFiles.length === 0) {
            this.showError('Please select TCX or GPX files.');
            return;
        }

        this.showLoading(true);

        for (const file of activityFiles) {
            try {
                await this.processActivityFile(file);
            } catch (error) {
                console.error(`Error processing ${file.name}:`, error);
                this.showError(`Error processing ${file.name}: ${error.message}`);
            }
        }

        this.showLoading(false);
        this.updateUI();
        this.fitMapToBounds();
    }

    async processActivityFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    const content = e.target.result;
                    const activity = file.name.toLowerCase().endsWith('.gpx')
                        ? this.parseGPX(content, file.name)
                        : this.parseTCX(content, file.name);
                    
                    if (activity && activity.trackpoints.length > 0) {
                        const activityId = this.generateActivityId();
                        this.activities.set(activityId, activity);
                        this.addActivityToMap(activityId, activity);
                        resolve(activity);
                    } else {
                        reject(new Error('No valid trackpoints found'));
                    }
                } catch (error) {
                    reject(error);
                }
            };
            
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }

    parseGPX(gpxContent, filename) {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(gpxContent, 'text/xml');
        const parseError = xmlDoc.querySelector('parsererror');

        if (parseError) {
            throw new Error('Invalid GPX XML');
        }

        const tracks = Array.from(xmlDoc.getElementsByTagNameNS('*', 'trk'));
        const routes = Array.from(xmlDoc.getElementsByTagNameNS('*', 'rte'));
        const containers = tracks.length > 0 ? tracks : routes;
        const pointTag = tracks.length > 0 ? 'trkpt' : 'rtept';

        if (containers.length === 0) {
            throw new Error('No tracks or routes found in GPX file');
        }

        const trackpoints = [];
        let totalDistance = 0;
        let totalTime = 0;

        for (const container of containers) {
            const segments = pointTag === 'trkpt'
                ? Array.from(container.getElementsByTagNameNS('*', 'trkseg'))
                : [container];
            const pointGroups = segments.length > 0 ? segments : [container];

            for (const group of pointGroups) {
                const points = Array.from(group.getElementsByTagNameNS('*', pointTag));
                let previousPoint = null;
                let firstTime = null;
                let lastTime = null;

                for (const point of points) {
                    const lat = Number.parseFloat(point.getAttribute('lat'));
                    const lng = Number.parseFloat(point.getAttribute('lon'));

                    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
                        continue;
                    }

                    const timeText = this.getFirstElementText(point, 'time');
                    const time = timeText ? new Date(timeText) : null;
                    const trackpoint = {
                        lat,
                        lng,
                        time: timeText || '',
                        altitude: this.parseOptionalNumber(this.getFirstElementText(point, 'ele')),
                        distance: null,
                        heartRate: this.parseOptionalNumber(this.getFirstElementText(point, 'hr'))
                    };

                    if (previousPoint) {
                        totalDistance += this.distanceBetween(previousPoint, trackpoint);
                    }
                    previousPoint = trackpoint;
                    trackpoints.push(trackpoint);

                    if (time && !Number.isNaN(time.getTime())) {
                        if (!firstTime) firstTime = time;
                        lastTime = time;
                    }
                }

                if (firstTime && lastTime) {
                    totalTime += Math.max(0, (lastTime - firstTime) / 1000);
                }
            }
        }

        if (trackpoints.length === 0) {
            throw new Error('No valid trackpoints found in GPX file');
        }

        const primaryContainer = containers[0];
        const type = this.getDirectChildText(primaryContainer, 'type');
        const name = this.getDirectChildText(primaryContainer, 'name');
        const firstTimedPoint = trackpoints.find(point => point.time);
        const firstPointTime = firstTimedPoint ? firstTimedPoint.time : '';
        const metadata = xmlDoc.getElementsByTagNameNS('*', 'metadata')[0];
        const metadataTime = metadata ? this.getDirectChildText(metadata, 'time') : '';
        const id = firstPointTime || metadataTime || '';
        const distance = this.formatDistance(totalDistance);

        return {
            filename,
            name: name || filename.replace(/\.gpx$/i, ''),
            format: 'GPX',
            sport: this.normalizeSport(type),
            id,
            startTime: id ? new Date(id) : null,
            duration: this.formatDuration(totalTime),
            distance: distance.value,
            distanceUnit: distance.unit,
            trackpoints,
            totalDistance,
            totalTime,
            bounds: this.calculateBounds(trackpoints)
        };
    }

    parseTCX(tcxContent, filename) {
        let tcxData;
        
        // Try to use fast-xml-parser library first, fallback to custom parser
        if (this.hasXMLParserLibrary && window.fxp && window.fxp.XMLParser) {
            const parser = new window.fxp.XMLParser(this.parserOptions);
            tcxData = parser.parse(tcxContent);
        } else {
            // Use fallback parser
            const parser = new FallbackXMLParser(this.parserOptions);
            tcxData = parser.parse(tcxContent);
        }

        console.log('Parsed TCX data structure:', tcxData);

        // Navigate through TCX structure - handle different possible structures
        let activities = null;
        
        // First, try the standard structure with TrainingCenterDatabase
        let trainingCenterDatabase = tcxData.TrainingCenterDatabase;
        if (trainingCenterDatabase && trainingCenterDatabase.Activities) {
            activities = trainingCenterDatabase.Activities;
        }
        
        // If not found, check for namespaced TrainingCenterDatabase elements
        if (!activities) {
            const rootKeys = Object.keys(tcxData);
            console.log('Available root keys:', rootKeys);
            
            for (const key of rootKeys) {
                if (key.includes('TrainingCenterDatabase') || key.includes('trainingcenterdatabase')) {
                    trainingCenterDatabase = tcxData[key];
                    if (trainingCenterDatabase && trainingCenterDatabase.Activities) {
                        activities = trainingCenterDatabase.Activities;
                        break;
                    }
                }
            }
        }
        
        // If still not found, check if Activities is directly at root level
        if (!activities && tcxData.Activities) {
            console.log('Found Activities directly at root level');
            activities = tcxData.Activities;
        }
        
        // Last resort: look for any key containing "activities"
        if (!activities) {
            const rootKeys = Object.keys(tcxData);
            for (const key of rootKeys) {
                if (key.toLowerCase().includes('activities') && !key.startsWith('@_')) {
                    console.log(`Found activities in key: ${key}`);
                    activities = tcxData[key];
                    break;
                }
            }
        }
        
        if (!activities) {
            console.error('TCX structure:', JSON.stringify(tcxData, null, 2));
            throw new Error(`No Activities found in TCX file. Available keys: ${Object.keys(tcxData).join(', ')}`);
        }

        const activityList = activities.Activity || activities;
        const activityData = Array.isArray(activityList) ? activityList[0] : activityList;

        if (!activityData) {
            throw new Error('No activity data found');
        }

        // Extract activity metadata
        const sport = activityData['@_Sport'] || 'Other';
        const id = activityData.Id || '';
        const laps = Array.isArray(activityData.Lap) ? activityData.Lap : [activityData.Lap];

        // Extract trackpoints from all laps
        const trackpoints = [];
        let totalDistance = 0;
        let totalTime = 0;

        for (const lap of laps) {
            if (!lap || !lap.Track) continue;

            const tracks = Array.isArray(lap.Track) ? lap.Track : [lap.Track];
            
            for (const track of tracks) {
                if (!track.Trackpoint) continue;
                
                const points = Array.isArray(track.Trackpoint) ? track.Trackpoint : [track.Trackpoint];
                
                for (const point of points) {
                    if (point.Position && point.Position.LatitudeDegrees && point.Position.LongitudeDegrees) {
                        trackpoints.push({
                            lat: parseFloat(point.Position.LatitudeDegrees),
                            lng: parseFloat(point.Position.LongitudeDegrees),
                            time: point.Time || '',
                            altitude: point.AltitudeMeters ? parseFloat(point.AltitudeMeters) : null,
                            distance: point.DistanceMeters ? parseFloat(point.DistanceMeters) : null,
                            heartRate: point.HeartRateBpm ? parseInt(point.HeartRateBpm.Value) : null
                        });
                    }
                }
            }

            // Accumulate lap statistics
            if (lap.TotalTimeSeconds) totalTime += parseFloat(lap.TotalTimeSeconds);
            if (lap.DistanceMeters) totalDistance += parseFloat(lap.DistanceMeters);
        }

        // Calculate additional metrics
        const startTime = new Date(id);
        const duration = this.formatDuration(totalTime);
        const distance = this.formatDistance(totalDistance);

        return {
            filename,
            name: filename.replace(/\.tcx$/i, ''),
            format: 'TCX',
            sport,
            id,
            startTime: Number.isNaN(startTime.getTime()) ? null : startTime,
            duration,
            distance: distance.value,
            distanceUnit: distance.unit,
            trackpoints,
            totalDistance,
            totalTime,
            bounds: this.calculateBounds(trackpoints)
        };
    }

    getFirstElementText(element, localName) {
        const match = element.getElementsByTagNameNS('*', localName)[0];
        return match ? match.textContent.trim() : '';
    }

    getDirectChildText(element, localName) {
        const match = Array.from(element.children).find(child => child.localName === localName);
        return match ? match.textContent.trim() : '';
    }

    parseOptionalNumber(value) {
        if (value === '') return null;
        const number = Number.parseFloat(value);
        return Number.isFinite(number) ? number : null;
    }

    normalizeSport(value) {
        const sport = (value || '').toLowerCase();

        if (sport.includes('run') || sport.includes('jog')) return 'Running';
        if (sport.includes('cycl') || sport.includes('bik')) return 'Cycling';
        if (sport.includes('walk') || sport.includes('hik')) return 'Walking';
        if (sport.includes('swim')) return 'Swimming';
        return 'Other';
    }

    distanceBetween(first, second) {
        const earthRadius = 6371000;
        const toRadians = degrees => degrees * Math.PI / 180;
        const lat1 = toRadians(first.lat);
        const lat2 = toRadians(second.lat);
        const deltaLat = toRadians(second.lat - first.lat);
        const deltaLng = toRadians(second.lng - first.lng);
        const a = Math.sin(deltaLat / 2) ** 2
            + Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLng / 2) ** 2;

        return earthRadius * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    addActivityToMap(activityId, activity) {
        if (activity.trackpoints.length === 0) return;

        const color = this.activityColors[activity.sport] || this.activityColors['Other'];
        const icon = this.activityIcons[activity.sport] || this.activityIcons['Other'];
        
        // Create polyline for the track
        const latlngs = activity.trackpoints.map(point => [point.lat, point.lng]);
        const polyline = L.polyline(latlngs, {
            color: color,
            weight: 3,
            opacity: 0.8
        }).addTo(this.map);

        // Create start marker
        const startPoint = activity.trackpoints[0];
        const startMarker = L.marker([startPoint.lat, startPoint.lng], {
            icon: L.divIcon({
                html: `<div style="background-color: ${color}; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"><i class="fas ${icon}"></i></div>`,
                className: 'custom-div-icon',
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            })
        }).addTo(this.map);

        // Add popup to start marker
        const popupContent = `
            <div style="min-width: 200px;">
                <h3 style="margin: 0 0 10px 0; color: ${color};">
                    <i class="fas ${icon}"></i> ${activity.sport}
                </h3>
                <p><strong>File:</strong> ${this.escapeHTML(activity.filename)}</p>
                <p><strong>Format:</strong> ${activity.format}</p>
                <p><strong>Date:</strong> ${this.formatDate(activity.startTime)}</p>
                <p><strong>Distance:</strong> ${activity.distance} ${activity.distanceUnit}</p>
                <p><strong>Duration:</strong> ${activity.duration}</p>
                <p><strong>Points:</strong> ${activity.trackpoints.length}</p>
            </div>
        `;
        
        startMarker.bindPopup(popupContent);

        // Store layer reference
        const layerGroup = L.layerGroup([polyline, startMarker]);
        this.activityLayers.set(activityId, layerGroup);

        // Update bounds
        if (activity.bounds) {
            this.bounds.extend(activity.bounds);
        }
    }

    calculateBounds(trackpoints) {
        if (trackpoints.length === 0) return null;
        
        const bounds = L.latLngBounds();
        trackpoints.forEach(point => {
            bounds.extend([point.lat, point.lng]);
        });
        return bounds;
    }

    generateActivityId() {
        return 'activity_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    updateUI() {
        this.updateActivityList();
        this.updateStats();
        this.updateActivityCount();
    }

    updateActivityList() {
        const activityList = document.getElementById('activityList');
        const emptyState = document.getElementById('emptyState');
        
        if (this.activities.size === 0) {
            emptyState.style.display = 'block';
            return;
        }
        
        emptyState.style.display = 'none';
        activityList.innerHTML = '';

        this.activities.forEach((activity, activityId) => {
            const activityItem = this.createActivityListItem(activityId, activity);
            activityList.appendChild(activityItem);
        });
    }

    createActivityListItem(activityId, activity) {
        const color = this.activityColors[activity.sport] || this.activityColors['Other'];
        const icon = this.activityIcons[activity.sport] || this.activityIcons['Other'];
        
        const item = document.createElement('div');
        item.className = 'activity-item';
        item.dataset.activityId = activityId;
        
        item.innerHTML = `
            <div class="activity-header">
                <div class="activity-icon" style="background-color: ${color};">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="activity-info">
                    <div class="activity-name">${this.escapeHTML(activity.name || activity.sport)}</div>
                    <div class="activity-details">${activity.format} • ${this.formatDate(activity.startTime)} • ${activity.distance} ${activity.distanceUnit}</div>
                </div>
            </div>
            <div class="activity-controls">
                <button class="btn btn-secondary" onclick="tcxVisualizer.toggleActivity('${activityId}')">
                    <i class="fas fa-eye"></i> Toggle
                </button>
                <button class="btn btn-secondary" onclick="tcxVisualizer.focusActivity('${activityId}')">
                    <i class="fas fa-search-location"></i> Focus
                </button>
                <button class="btn btn-secondary" onclick="tcxVisualizer.removeActivity('${activityId}')">
                    <i class="fas fa-trash"></i> Remove
                </button>
            </div>
        `;

        return item;
    }

    updateStats() {
        const statsSection = document.getElementById('statsSection');
        const statsContent = document.getElementById('statsContent');
        
        if (this.activities.size === 0) {
            statsSection.style.display = 'none';
            return;
        }

        statsSection.style.display = 'block';
        
        const stats = this.calculateOverallStats();
        
        statsContent.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Total Activities:</span>
                <span class="stat-value">${stats.totalActivities}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Total Distance:</span>
                <span class="stat-value">${stats.totalDistance}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Total Time:</span>
                <span class="stat-value">${stats.totalTime}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Most Common:</span>
                <span class="stat-value">${stats.mostCommonSport}</span>
            </div>
        `;
    }

    calculateOverallStats() {
        let totalDistance = 0;
        let totalTime = 0;
        const sportCounts = {};

        this.activities.forEach(activity => {
            totalDistance += activity.totalDistance || 0;
            totalTime += activity.totalTime || 0;
            
            sportCounts[activity.sport] = (sportCounts[activity.sport] || 0) + 1;
        });

        const mostCommonSport = Object.keys(sportCounts).reduce((a, b) => 
            sportCounts[a] > sportCounts[b] ? a : b, 'None'
        );

        return {
            totalActivities: this.activities.size,
            totalDistance: this.formatDistance(totalDistance).display,
            totalTime: this.formatDuration(totalTime),
            mostCommonSport
        };
    }

    updateActivityCount() {
        const activityCount = document.getElementById('activityCount');
        activityCount.textContent = this.activities.size;
    }

    toggleActivity(activityId) {
        const layer = this.activityLayers.get(activityId);
        const activityItem = document.querySelector(`[data-activity-id="${activityId}"]`);
        
        if (!layer || !activityItem) return;

        if (this.map.hasLayer(layer)) {
            this.map.removeLayer(layer);
            activityItem.classList.add('hidden');
        } else {
            this.map.addLayer(layer);
            activityItem.classList.remove('hidden');
        }
    }

    focusActivity(activityId) {
        const activity = this.activities.get(activityId);
        if (!activity || !activity.bounds) return;

        this.map.fitBounds(activity.bounds, { padding: [20, 20] });
    }

    removeActivity(activityId) {
        const layer = this.activityLayers.get(activityId);
        const activityItem = document.querySelector(`[data-activity-id="${activityId}"]`);
        
        if (layer) {
            this.map.removeLayer(layer);
            this.activityLayers.delete(activityId);
        }
        
        if (activityItem) {
            activityItem.remove();
        }
        
        this.activities.delete(activityId);
        this.updateUI();
        
        if (this.activities.size > 0) {
            this.recalculateBounds();
            this.fitMapToBounds();
        }
    }

    recalculateBounds() {
        this.bounds = L.latLngBounds();
        this.activities.forEach(activity => {
            if (activity.bounds) {
                this.bounds.extend(activity.bounds);
            }
        });
    }

    fitMapToBounds() {
        if (this.bounds.isValid()) {
            this.map.fitBounds(this.bounds, { padding: [20, 20] });
        }
    }

    formatDistance(meters) {
        if (!meters || meters === 0) return { value: '0', unit: 'km', display: '0 km' };
        
        if (meters < 1000) {
            return { 
                value: Math.round(meters), 
                unit: 'm', 
                display: `${Math.round(meters)} m` 
            };
        } else {
            const km = (meters / 1000).toFixed(2);
            return { 
                value: km, 
                unit: 'km', 
                display: `${km} km` 
            };
        }
    }

    formatDuration(seconds) {
        if (!seconds || seconds === 0) return '0:00';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }

    formatDate(date) {
        return date && !Number.isNaN(date.getTime()) ? date.toLocaleDateString() : 'Unknown date';
    }

    escapeHTML(value) {
        const element = document.createElement('div');
        element.textContent = String(value);
        return element.innerHTML;
    }

    showLoading(show) {
        // Could add a loading spinner here
        console.log(show ? 'Loading...' : 'Loading complete');
    }

    showError(message) {
        // Create error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
        
        const sidebar = document.querySelector('.sidebar');
        sidebar.insertBefore(errorDiv, sidebar.firstChild);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
}

// Fallback XML Parser implementation using DOMParser (fallback if fast-xml-parser is not available)
class FallbackXMLParser {
    constructor(options) {
        this.options = options;
    }

    parse(xmlString) {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlString, 'text/xml');
        
        // Check for parsing errors
        const parseError = xmlDoc.querySelector('parsererror');
        if (parseError) {
            throw new Error('XML parsing error: ' + parseError.textContent);
        }
        
        return this.xmlToJson(xmlDoc.documentElement);
    }

    xmlToJson(xml) {
        const result = {};
        
        // Add attributes
        if (xml.attributes) {
            for (let attr of xml.attributes) {
                result['@_' + attr.name] = attr.value;
            }
        }
        
        // Process child nodes
        const childNodes = Array.from(xml.childNodes).filter(node => 
            node.nodeType === Node.ELEMENT_NODE
        );
        
        if (childNodes.length === 0) {
            // Leaf node with text content
            const textContent = xml.textContent.trim();
            return textContent || result;
        }
        
        for (let child of childNodes) {
            const childName = child.nodeName;
            const childValue = this.xmlToJson(child);
            
            if (result[childName]) {
                // Multiple children with same name - convert to array
                if (!Array.isArray(result[childName])) {
                    result[childName] = [result[childName]];
                }
                result[childName].push(childValue);
            } else {
                result[childName] = childValue;
            }
        }
        
        return result;
    }
}

// Initialize the application when the page loads
let tcxVisualizer;

document.addEventListener('DOMContentLoaded', function() {
    tcxVisualizer = new TCXVisualizer();
});

// Export for global access
window.tcxVisualizer = tcxVisualizer; 