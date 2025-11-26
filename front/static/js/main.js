let map;
let activeLayers = {};
let locationMarker = null;
let pickingLocationFor = null;

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadTracks();
    setupFileInputListener();
    setupMapClickHandler();
    setupSidebarControls();
});

function initMap() {
    map = L.map('map').setView([0, 0], 2);

    // Define base layers
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    });

    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles © Esri',
        maxZoom: 19
    });

    const topoLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap',
        maxZoom: 17
    });

    const stamenTerrain = L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png', {
        attribution: '© Stamen Design © OpenStreetMap contributors',
        maxZoom: 18
    });

    const cyclOSM = L.tileLayer('https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors © CyclOSM',
        maxZoom: 20
    });

    // Add default layer
    osmLayer.addTo(map);

    // Create layer control
    const baseMaps = {
        "Street Map": osmLayer,
        "Satellite": satelliteLayer,
        "Topographic": topoLayer,
        "Terrain": stamenTerrain,
        "Cycling": cyclOSM
    };

    L.control.layers(baseMaps).addTo(map);
}

async function uploadGPX() {
    const input = document.getElementById('gpxInput');
    const categorySelect = document.getElementById('categorySelect');

    if (input.files.length === 0) {
        alert('Please select a file');
        return;
    }

    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < input.files.length; i++) {
        const file = input.files[i];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', categorySelect.value);

        const lat = document.getElementById('latitudeInput').value;
        const lon = document.getElementById('longitudeInput').value;
        if (lat) formData.append('latitude', lat);
        if (lon) formData.append('longitude', lon);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                successCount++;
            } else {
                failCount++;
                console.error(`Failed to upload ${file.name}`);
            }
        } catch (error) {
            failCount++;
            console.error(`Error uploading ${file.name}:`, error);
        }
    }

    if (successCount > 0) {
        alert(`Successfully uploaded ${successCount} file(s)${failCount > 0 ? `, ${failCount} failed` : ''}`);
        loadTracks();
        input.value = '';
        // Clear location inputs
        document.getElementById('latitudeInput').value = '';
        document.getElementById('longitudeInput').value = '';
        if (locationMarker) {
            map.removeLayer(locationMarker);
            locationMarker = null;
        }
    } else {
        alert('All uploads failed');
    }
}

async function loadTracks() {
    try {
        const response = await fetch('/api/tracks');
        const data = await response.json();
        const list = document.getElementById('trackList');
        list.innerHTML = '';

        const tree = buildTrackTree(data.tracks);
        renderTrackTree(tree, list);
    } catch (error) {
        console.error('Error loading tracks:', error);
        alert('Error loading tracks: ' + error.message);
    }
}

function buildTrackTree(tracks) {
    console.log('Building track tree with tracks:', tracks);
    const tree = {
        'trail': {},
        'enduro': {},
        'special_events': {},
        'media': {}
    };
    tracks.sort().forEach(path => {
        const parts = path.split('/');

        // Handle media files with subfolders: media/subfolder/filename
        if (parts[0] === 'media') {
            if (parts.length === 2) {
                // Direct media file: media/filename
                if (!tree['media']['Root']) tree['media']['Root'] = [];
                tree['media']['Root'].push({ filename: parts[1], fullPath: path });
            } else if (parts.length === 3) {
                // Subfolder media file: media/subfolder/filename
                const subfolder = parts[1];
                if (!tree['media'][subfolder]) tree['media'][subfolder] = [];
                tree['media'][subfolder].push({ filename: parts[2], fullPath: path });
            } else if (parts.length > 3) {
                // Nested subfolders: media/subfolder1/subfolder2/.../filename
                // We'll flatten to just one level for simplicity
                const subfolder = parts.slice(1, -1).join('/');
                if (!tree['media'][subfolder]) tree['media'][subfolder] = [];
                tree['media'][subfolder].push({ filename: parts[parts.length - 1], fullPath: path });
            }
        }
        // Handle track files: category/year/month/filename
        else if (parts.length === 4) {
            const [category, year, month, filename] = parts;
            if (!tree[category]) tree[category] = {};
            if (!tree[category][year]) tree[category][year] = {};
            if (!tree[category][year][month]) tree[category][year][month] = [];
            tree[category][year][month].push({ filename, fullPath: path });
        }
        // Handle legacy or unexpected structure
        else {
            if (!tree['Uncategorized']) tree['Uncategorized'] = {};
            if (!tree['Uncategorized']['Others']) tree['Uncategorized']['Others'] = {};
            if (!tree['Uncategorized']['Others']['Files']) tree['Uncategorized']['Others']['Files'] = [];
            tree['Uncategorized']['Others']['Files'].push({ filename: path, fullPath: path });
        }
    });
    return tree;
}

function renderTrackTree(tree, container) {
    // Orden personalizado de categorías
    const categoryOrder = ['enduro', 'trail', 'special_events', 'media'];

    // Obtener categorías en el orden deseado, luego las que no estén en la lista
    const orderedCategories = categoryOrder.filter(cat => tree[cat]);
    const otherCategories = Object.keys(tree).filter(cat => !categoryOrder.includes(cat)).sort();
    const allCategories = [...orderedCategories, ...otherCategories];

    // Categories
    allCategories.forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category-group';

        const categoryHeader = document.createElement('div');
        categoryHeader.className = 'category-header';

        const groupData = tree[category];
        let categoryCount = 0;

        if (Array.isArray(groupData)) {
            categoryCount = groupData.length;
        } else {
            const years = groupData;
            Object.values(years).forEach(months => {
                if (Array.isArray(months)) {
                    categoryCount += months.length;
                } else {
                    Object.values(months).forEach(files => categoryCount += files.length);
                }
            });
        }

        categoryHeader.innerHTML = `
            <div style="display: flex; align-items: center;">
                <span class="chevron collapsed">▼</span>
                <input type="checkbox" class="checkbox category-checkbox" onclick="event.stopPropagation()">
                <span>${formatCategoryName(category)}</span>
            </div>
            <span class="group-count">${categoryCount}</span>
        `;

        const categoryCheckbox = categoryHeader.querySelector('.category-checkbox');
        categoryCheckbox.onchange = (e) => toggleGroup(e, groupData, categoryCheckbox);

        categoryHeader.onclick = (e) => toggleCollapse(e, categoryDiv);

        // Hover effects
        categoryHeader.onmouseenter = () => highlightGroup(groupData);
        categoryHeader.onmouseleave = () => resetGroupStyle(groupData);

        categoryDiv.appendChild(categoryHeader);

        const contentContainer = document.createElement('div');
        contentContainer.className = 'group-content collapsed';

        if (Array.isArray(groupData)) {
            // Render files directly
            groupData.forEach(file => {
                const trackDiv = createTrackItemElement(file);
                contentContainer.appendChild(trackDiv);
            });
        } else if (category === 'media') {
            // Special handling for media: render subfolders directly
            Object.keys(groupData).sort().forEach(subfolder => {
                const files = groupData[subfolder];

                const subfolderDiv = document.createElement('div');
                subfolderDiv.className = 'year-group'; // Reuse year-group styling

                const subfolderHeader = document.createElement('div');
                subfolderHeader.className = 'year-header';

                subfolderHeader.innerHTML = `
                    <div style="display: flex; align-items: center;">
                        <span class="chevron collapsed">▼</span>
                        <input type="checkbox" class="checkbox year-checkbox" onclick="event.stopPropagation()">
                        <span>${subfolder}</span>
                    </div>
                    <span class="group-count">${files.length}</span>
                `;

                const subfolderCheckbox = subfolderHeader.querySelector('.year-checkbox');
                subfolderCheckbox.onchange = (e) => toggleGroup(e, files, subfolderCheckbox);

                subfolderHeader.onclick = (e) => toggleCollapse(e, subfolderDiv);

                // Hover effects
                subfolderHeader.onmouseenter = () => highlightGroup(files);
                subfolderHeader.onmouseleave = () => resetGroupStyle(files);

                subfolderDiv.appendChild(subfolderHeader);

                const filesContainer = document.createElement('div');
                filesContainer.className = 'group-content collapsed';

                // Render files directly
                files.forEach(file => {
                    const trackDiv = createTrackItemElement(file);
                    filesContainer.appendChild(trackDiv);
                });

                subfolderDiv.appendChild(filesContainer);
                contentContainer.appendChild(subfolderDiv);
            });
        } else {
            // Existing Year/Month logic for tracks
            const years = groupData;
            Object.keys(years).sort((a, b) => b - a).forEach(year => {
                const yearDiv = document.createElement('div');
                yearDiv.className = 'year-group';

                const yearHeader = document.createElement('div');
                yearHeader.className = 'year-header';
                const months = years[year];

                let yearCount = 0;
                Object.values(months).forEach(files => yearCount += files.length);

                yearHeader.innerHTML = `
                    <div style="display: flex; align-items: center;">
                        <span class="chevron collapsed">▼</span>
                        <input type="checkbox" class="checkbox year-checkbox" onclick="event.stopPropagation()">
                        <span>${year}</span>
                    </div>
                    <span class="group-count">${yearCount}</span>
                `;

                const yearCheckbox = yearHeader.querySelector('.year-checkbox');
                yearCheckbox.onchange = (e) => toggleGroup(e, months, yearCheckbox);

                yearHeader.onclick = (e) => toggleCollapse(e, yearDiv);

                // Hover effects
                yearHeader.onmouseenter = () => highlightGroup(months);
                yearHeader.onmouseleave = () => resetGroupStyle(months);

                yearDiv.appendChild(yearHeader);

                const monthsContainer = document.createElement('div');
                monthsContainer.className = 'group-content collapsed';

                // Months
                Object.keys(months).sort((a, b) => b - a).forEach(month => {
                    const monthDiv = document.createElement('div');
                    monthDiv.className = 'month-group';

                    const monthHeader = document.createElement('div');
                    monthHeader.className = 'month-header';
                    const files = months[month];

                    monthHeader.innerHTML = `
                        <div style="display: flex; align-items: center;">
                            <span class="chevron collapsed">▼</span>
                            <input type="checkbox" class="checkbox month-checkbox" onclick="event.stopPropagation()">
                            <span>${getMonthName(month)}</span>
                        </div>
                        <span class="group-count">${files.length}</span>
                    `;

                    const monthCheckbox = monthHeader.querySelector('.month-checkbox');
                    monthCheckbox.onchange = (e) => toggleGroup(e, files, monthCheckbox);

                    monthHeader.onclick = (e) => toggleCollapse(e, monthDiv);

                    // Hover effects
                    monthHeader.onmouseenter = () => highlightGroup(files);
                    monthHeader.onmouseleave = () => resetGroupStyle(files);

                    monthDiv.appendChild(monthHeader);

                    const tracksContainer = document.createElement('div');
                    tracksContainer.className = 'group-content collapsed';

                    // Files - check if it's an array
                    if (Array.isArray(files)) {
                        files.forEach(file => {
                            const trackDiv = createTrackItemElement(file);
                            tracksContainer.appendChild(trackDiv);
                        });
                    } else {
                        // If files is an object (nested structure), skip or handle differently
                        console.warn('Unexpected nested structure at month level:', month, files);
                    }

                    monthDiv.appendChild(tracksContainer);
                    monthsContainer.appendChild(monthDiv);
                });
                yearDiv.appendChild(monthsContainer);
                contentContainer.appendChild(yearDiv);
            });
        }
        categoryDiv.appendChild(contentContainer);
        container.appendChild(categoryDiv);
    });
}

function formatCategoryName(category) {
    // Mapeo especial para categorías
    const categoryMap = {
        'special_events': 'Eventos',
        'trail': 'Trail',
        'enduro': 'Enduro',
        'fotos': 'Fotos',
        'videos': 'Videos',
        'media': 'Media'
    };

    if (categoryMap[category]) {
        return categoryMap[category];
    }

    // Fallback: convertir snake_case a Title Case
    return category.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function toggleCollapse(event, container) {
    event.stopPropagation();
    const content = container.querySelector('.group-content');
    const chevron = container.querySelector('.chevron');

    if (content) {
        content.classList.toggle('collapsed');
        if (chevron) {
            chevron.classList.toggle('collapsed');
        }
    }
}

function getMonthName(monthNum) {
    if (isNaN(monthNum)) return monthNum;
    const date = new Date(2000, parseInt(monthNum) - 1, 1);
    return date.toLocaleString('default', { month: 'long' });
}

async function toggleGroup(event, groupData, checkbox) {
    event.stopPropagation();

    let files = [];

    // Helper to collect all files recursively
    function collectFiles(data) {
        if (Array.isArray(data)) {
            files.push(...data);
        } else {
            Object.values(data).forEach(child => collectFiles(child));
        }
    }

    collectFiles(groupData);

    // Check if all tracks in this group are already visible
    const allVisible = files.every(f => activeLayers[f.fullPath]);

    // If user is checking but all are already visible, uncheck them instead
    if (checkbox.checked && allVisible) {
        checkbox.checked = false;
    }

    const shouldAdd = checkbox.checked;

    if (!shouldAdd) {
        // Remove all
        files.forEach(f => {
            if (activeLayers[f.fullPath]) {
                map.removeLayer(activeLayers[f.fullPath]);
                delete activeLayers[f.fullPath];
            }
        });
    } else {
        // Add all (that are not already active)
        for (const f of files) {
            if (!activeLayers[f.fullPath]) {
                try {
                    const response = await fetch(`/api/track/${f.fullPath}`);
                    const geojson = await response.json();
                    const layer = createLayerFromGeoJSON(geojson, f.fullPath);
                    activeLayers[f.fullPath] = layer;
                } catch (e) {
                    console.error("Failed to load", f.fullPath);
                }
            }
        }
    }
    // Don't re-render the entire tree, just update checkboxes manually
    updateCheckboxStates();
}

function updateCheckboxStates() {
    // Update all checkboxes to reflect current active layers
    document.querySelectorAll('.track-checkbox').forEach(checkbox => {
        const trackItem = checkbox.closest('.track-item');
        if (trackItem) {
            const filename = trackItem.dataset.filename;
            checkbox.checked = !!activeLayers[filename];
            if (activeLayers[filename]) {
                trackItem.classList.add('active');
            } else {
                trackItem.classList.remove('active');
            }
        }
    });
}

// Función reutilizable para crear una capa desde GeoJSON
function createLayerFromGeoJSON(geojson, filename) {
    let layer;

    // Check if it's a Point geometry (Photo or Video)
    if (geojson.features && geojson.features[0].geometry.type === 'Point') {
        const coords = geojson.features[0].geometry.coordinates; // lon, lat
        layer = L.marker([coords[1], coords[0]]).addTo(map);

        const props = geojson.features[0].properties;
        // Use dynamic repository base URL
        const repoBase = window.REPO_BASE_URL || '/uploads';
        const mediaUrl = `${repoBase}/${filename}`;
        const fileName = filename.split('/').pop();
        const isVideo = props.type === 'video';

        // Crear popup con contenido básico, se completará dinámicamente
        const popupDiv = document.createElement('div');
        popupDiv.style.cssText = 'text-align: center; min-width: 200px;';
        popupDiv.innerHTML = `
            < h4 style = "margin: 5px 0 10px 0; font-size: 14px; word-break: break-word;" > ${isVideo ? (props.name || fileName) : fileName
            }</h4 >
            <div id="media-container-${filename.replace(/[^a-zA-Z0-9]/g, '-')}" style="position: relative; background: ${isVideo ? '#000' : '#f0f0f0'}; border-radius: 4px; overflow: hidden; margin: 0 auto; width: 200px; height: 150px; display: flex; align-items: center; justify-content: center; border: 2px solid ${isVideo ? '#333' : '#ddd'};">
                <div style="color: ${isVideo ? '#fff' : '#999'}; font-size: 12px;">Cargando...</div>
            </div>
            <p style="margin: 8px 0 0 0; color: #666; font-size: 12px;">${isVideo ? '📹' : '🖼️'} Haz clic para ${isVideo ? 'abrir el video' : 'ver tamaño completo'}</p>
        `;

        layer.bindPopup(popupDiv, { maxWidth: 300, minWidth: 200 });

        // Crear contenido dinámicamente cuando se abre el popup
        layer.on('popupopen', function () {
            const containerId = `media-container-${filename.replace(/[^a-zA-Z0-9]/g, '-')}`;
            const container = document.getElementById(containerId);
            if (!container) return;

            if (isVideo) {
                // Crear video element dinámicamente
                const link = document.createElement('a');
                link.href = mediaUrl;
                link.target = '_blank';
                link.style.cssText = 'display: block; text-decoration: none; cursor: pointer; width: 100%; height: 100%;';
                link.onclick = (e) => e.stopPropagation();

                const video = document.createElement('video');
                video.style.cssText = 'width: 100%; height: 100%; object-fit: contain; pointer-events: none; opacity: 0; transition: opacity 0.3s;';
                video.preload = 'metadata';
                video.muted = true;
                video.playsInline = true;

                const source = document.createElement('source');
                source.src = mediaUrl;
                source.type = 'video/mp4';
                video.appendChild(source);

                // Botón de play
                const playBtn = document.createElement('div');
                playBtn.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.7); border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; pointer-events: none; z-index: 10; border: 2px solid rgba(255,255,255,0.3);';
                playBtn.innerHTML = '<span style="color: white; font-size: 24px; margin-left: 3px;">▶</span>';

                link.appendChild(video);
                link.appendChild(playBtn);
                container.innerHTML = '';
                container.appendChild(link);

                // Cargar primer frame
                video.addEventListener('loadedmetadata', function () {
                    this.currentTime = 0.1;
                }, { once: true });

                video.addEventListener('seeked', function () {
                    this.pause();
                    this.style.opacity = '1';
                }, { once: true });

                video.addEventListener('error', function () {
                    container.innerHTML = '<div style="color: #f00; padding: 20px;">❌ Error al cargar video</div>';
                }, { once: true });
            } else {
                // Crear imagen dinámicamente
                const link = document.createElement('a');
                link.href = mediaUrl;
                link.target = '_blank';
                link.style.cssText = 'display: block; text-decoration: none; cursor: pointer; width: 100%; height: 100%;';
                link.onclick = (e) => e.stopPropagation();

                const img = document.createElement('img');
                img.src = mediaUrl;
                img.style.cssText = 'max-width: 200px; max-height: 150px; width: auto; height: auto; object-fit: contain; border-radius: 4px; cursor: pointer; opacity: 0; transition: opacity 0.3s;';

                img.onload = function () {
                    this.style.opacity = '1';
                };

                img.onerror = function () {
                    this.onerror = null;
                    this.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="150"%3E%3Crect fill="%23ddd" width="200" height="150"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy="0.3em" fill="%23999" font-size="14"%3EError%3C/text%3E%3C/svg%3E';
                    this.style.opacity = '1';
                };

                link.appendChild(img);
                container.innerHTML = '';
                container.appendChild(link);
            }
        });

        layer.on('click', () => highlightSidebarItem(filename));
    } else {
        // It's a track
        layer = L.geoJSON(geojson, {
            style: {
                color: getTrackColor(filename),
                weight: 2,
                opacity: 1
            }
        }).bindPopup(filename.split('/').pop()).on('click', () => highlightSidebarItem(filename)).addTo(map);
    }

    return layer;
}

async function toggleTrack(filename, element, checkbox) {
    if (activeLayers[filename]) {
        // Remove track
        map.removeLayer(activeLayers[filename]);
        delete activeLayers[filename];
        element.classList.remove('active');
        if (checkbox) checkbox.checked = false;
    } else {
        // Add track
        try {
            const response = await fetch(`/ api / track / ${filename} `);
            const geojson = await response.json();
            const layer = createLayerFromGeoJSON(geojson, filename);

            activeLayers[filename] = layer;
            element.classList.add('active');
            if (checkbox) checkbox.checked = true;
        } catch (error) {
            console.error('Error loading track:', error);
            alert('Could not load track on map');
        }
    }
}

function fitAllBounds() {
    const layers = Object.values(activeLayers);
    if (layers.length > 0) {
        const group = L.featureGroup(layers);
        map.fitBounds(group.getBounds());
    }
}

function getTrackColor(path) {
    const parts = path.split('/');
    if (parts.length > 0) {
        const category = parts[0].toLowerCase();
        if (category === 'enduro') return '#FF0000';
        if (category === 'trail') return '#FFD700';
    }
    return getRandomColor();
}

function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function highlightTrack(filename) {
    if (activeLayers[filename] && activeLayers[filename].setStyle) {
        activeLayers[filename].setStyle({
            color: '#00FFFF',
            weight: 6
        });
        activeLayers[filename].bringToFront();
    }
}

function resetTrackStyle(filename) {
    if (activeLayers[filename] && activeLayers[filename].setStyle) {
        activeLayers[filename].setStyle({
            color: getTrackColor(filename),
            weight: 2
        });
    }
}

function highlightGroup(groupData) {
    if (Array.isArray(groupData)) {
        groupData.forEach(file => highlightTrack(file.fullPath));
    } else {
        Object.values(groupData).forEach(child => highlightGroup(child));
    }
}

function resetGroupStyle(groupData) {
    if (Array.isArray(groupData)) {
        groupData.forEach(file => resetTrackStyle(file.fullPath));
    } else {
        Object.values(groupData).forEach(child => resetGroupStyle(child));
    }
}

function highlightSidebarItem(filename) {
    const previous = document.querySelector('.track-item.selected');
    if (previous) {
        previous.classList.remove('selected');
    }

    const item = document.querySelector(`.track - item[data - filename="${filename}"]`);
    if (item) {
        item.classList.add('selected');
        item.scrollIntoView({ behavior: 'smooth', block: 'center' });

        let parent = item.parentElement;
        while (parent) {
            if (parent.classList.contains('collapsed')) {
                parent.classList.remove('collapsed');
            }
            parent = parent.parentElement;
        }
    }
}

function setupFileInputListener() {
    const fileInput = document.getElementById('gpxInput');
    const manualLocation = document.getElementById('manualLocation');

    fileInput.addEventListener('change', (e) => {
        const files = e.target.files;
        let hasVideo = false;

        for (let file of files) {
            const fileName = file.name.toLowerCase();
            if (fileName.endsWith('.mp4') || fileName.endsWith('.mov') ||
                fileName.endsWith('.avi') || fileName.endsWith('.mkv')) {
                hasVideo = true;
                break;
            }
        }

        if (hasVideo) {
            manualLocation.style.display = 'flex';
        } else {
            manualLocation.style.display = 'none';
            document.getElementById('latitudeInput').value = '';
            document.getElementById('longitudeInput').value = '';
            if (locationMarker) {
                map.removeLayer(locationMarker);
                locationMarker = null;
            }
        }
    });
}

function setupMapClickHandler() {
    const manualLocation = document.getElementById('manualLocation');

    map.on('click', async (e) => {
        // Handle "Pick Location" mode
        if (pickingLocationFor) {
            const lat = e.latlng.lat;
            const lng = e.latlng.lng;

            if (confirm(`Set location for ${pickingLocationFor} to[${lat.toFixed(6)}, ${lng.toFixed(6)}]?`)) {
                try {
                    const response = await fetch(`/ api / media / ${pickingLocationFor}/location`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            latitude: lat,
                            longitude: lng
                        })
                    });

                    if (response.ok) {
                        alert('Location updated successfully!');

                        // Reload the track/media if it was active
                        if (activeLayers[pickingLocationFor]) {
                            map.removeLayer(activeLayers[pickingLocationFor]);
                            delete activeLayers[pickingLocationFor];

                            // Re-add it to show new location
                            const checkbox = document.querySelector(`.track-item[data-filename="${pickingLocationFor}"] .track-checkbox`);
                            if (checkbox) {
                                checkbox.checked = true; // Ensure it stays checked
                                toggleTrack(pickingLocationFor, checkbox.closest('.track-item'), checkbox);
                            }
                        }
                    } else {
                        const data = await response.json();
                        alert('Failed to update location: ' + (data.detail || 'Unknown error'));
                    }
                } catch (error) {
                    console.error('Error updating location:', error);
                    alert('Error updating location');
                }
            }

            // Exit pick mode
            pickingLocationFor = null;
            document.getElementById('map').style.cursor = '';
            return;
        }

        if (manualLocation.style.display !== 'none') {
            const lat = e.latlng.lat.toFixed(6);
            const lng = e.latlng.lng.toFixed(6);

            document.getElementById('latitudeInput').value = lat;
            document.getElementById('longitudeInput').value = lng;

            if (locationMarker) {
                map.removeLayer(locationMarker);
            }

            locationMarker = L.marker([e.latlng.lat, e.latlng.lng], {
                icon: L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                })
            }).addTo(map);

            locationMarker.bindPopup(`Ubicación seleccionada:<br>Lat: ${lat}<br>Lng: ${lng}`).openPopup();
        }
    });
}

function enableLocationPicker(filename) {
    pickingLocationFor = filename;
    document.getElementById('map').style.cursor = 'crosshair';
    alert(`Click on the map to set the location for ${filename}`);
}

function createTrackItemElement(file) {
    const trackDiv = document.createElement('div');
    trackDiv.className = 'track-item';
    trackDiv.dataset.filename = file.fullPath;

    const isChecked = !!activeLayers[file.fullPath];
    trackDiv.innerHTML = `
        <input type="checkbox" class="checkbox track-checkbox" ${isChecked ? 'checked' : ''}>
        <span>${file.filename}</span>
    `;

    // Add Set Location button for all media files (images and videos)
    const isMedia = /\.(jpg|jpeg|png|gif|webp|mp4|mov|avi|mkv)$/i.test(file.filename);
    if (isMedia) {
        const setLocBtn = document.createElement('button');
        setLocBtn.innerHTML = '📍';
        setLocBtn.title = 'Set Location';
        setLocBtn.className = 'set-location-btn';
        setLocBtn.style.cssText = 'margin-left: auto; background: none; border: none; cursor: pointer; opacity: 0.6; padding: 0 5px;';
        setLocBtn.onclick = (e) => {
            e.stopPropagation();
            enableLocationPicker(file.fullPath);
        };
        trackDiv.appendChild(setLocBtn);
    }

    if (isChecked) {
        trackDiv.classList.add('active');
    }

    const trackCheckbox = trackDiv.querySelector('.track-checkbox');
    trackCheckbox.onchange = (e) => {
        e.stopPropagation();
        toggleTrack(file.fullPath, trackDiv, trackCheckbox);
    };

    trackDiv.onclick = (e) => {
        if (e.target !== trackCheckbox) {
            if (isMedia) {
                window.open(`/uploads/${file.fullPath}`, '_blank');
            } else {
                trackCheckbox.checked = !trackCheckbox.checked;
                trackCheckbox.dispatchEvent(new Event('change'));
            }
        }
    };

    // Hover effects
    trackDiv.onmouseenter = () => highlightTrack(file.fullPath);
    trackDiv.onmouseleave = () => resetTrackStyle(file.fullPath);

    return trackDiv;
}

function setupSidebarControls() {
    const sidebar = document.getElementById('sidebar');
    const resizer = document.getElementById('resizer');
    const toggleBtn = document.getElementById('sidebarToggle');

    let isResizing = false;
    let lastDownX = 0;

    // Resizer functionality
    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        lastDownX = e.clientX;
        resizer.classList.add('resizing');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;

        const offsetX = e.clientX - lastDownX;
        const newWidth = sidebar.offsetWidth + offsetX;

        // Constrain width between 200px and 600px
        if (newWidth >= 200 && newWidth <= 600) {
            sidebar.style.width = newWidth + 'px';
            lastDownX = e.clientX;

            // Invalidate map size to adjust to new sidebar width
            if (map) {
                setTimeout(() => map.invalidateSize(), 0);
            }
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            resizer.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });

    // Toggle functionality
    toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');

        // Update toggle button icon
        if (sidebar.classList.contains('collapsed')) {
            toggleBtn.textContent = '☰';
        } else {
            toggleBtn.textContent = '✕';
        }

        // Invalidate map size to adjust to sidebar visibility
        setTimeout(() => {
            if (map) map.invalidateSize();
        }, 100);
    });
}
