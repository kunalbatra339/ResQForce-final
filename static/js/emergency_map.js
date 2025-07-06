// Ensure Leaflet is loaded before this script runs
// const L = window.L; // If Leaflet is globally available

// Initialize map
const map = L.map('map', {
    center: [20.5937, 78.9629],
    zoom: 5,
    zoomControl: false
});

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
}).addTo(map);

L.control.zoom({ position: 'topright' }).addTo(map);

let emergencyMarkers = [];

async function loadEmergencies() {
    try {
        console.log('[DEBUG] Fetching emergencies...');
        emergencyMarkers.forEach(m => map.removeLayer(m));
        emergencyMarkers = [];

        const response = await fetch('/api/emergency_details');
        if (!response.ok) {
            console.error('API Error:', response.status);
            displayMessage('Error loading emergencies.', 'error');
            return;
        }

        const emergencies = await response.json();
        console.log('[DEBUG] Emergency Data:', emergencies);

        if (emergencies.length === 0) {
            console.warn('No emergencies found');
            displayMessage('No pending emergencies found.', 'info'); // Use info for no emergencies
            return;
        }

        emergencies.forEach(emergency => {
            try {
                const lat = parseFloat(emergency.latitude);
                const lng = parseFloat(emergency.longitude);
                if (isNaN(lat) || isNaN(lng)) throw 'Invalid coordinates';

                const marker = L.marker([lat, lng], {
                    icon: L.icon({
                        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
                        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
                        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
                        iconSize: [25, 41],
                        iconAnchor: [12, 41],
                        popupAnchor: [1, -34]
                    })
                }).bindPopup(`
                    <b>${emergency.severity_display}</b><br>
                    ${emergency.description}<br>
                    Coordinates: ${lat.toFixed(4)}, ${lng.toFixed(4)}
                `);

                marker.addTo(map);
                emergencyMarkers.push(marker);
            } catch (e) {
                console.error('Marker Error:', e, emergency);
            }
        });

        const group = new L.featureGroup(emergencyMarkers);
        map.fitBounds(group.getBounds().pad(0.2));
        displayMessage('', ''); // Clear any previous messages
    } catch (error) {
        console.error('Critical Error:', error);
        displayMessage('Failed to load emergencies due to a critical error.', 'error');
    }
}

// Function to display messages on the page
function displayMessage(message, type) {
    const statusMessageDiv = document.getElementById('status-message');
    if (statusMessageDiv) { // Ensure the element exists
        statusMessageDiv.textContent = message;
        statusMessageDiv.className = `message-box ${type} ${message ? '' : 'hidden'}`;
        if (message) {
            setTimeout(() => {
                statusMessageDiv.classList.add('hidden');
            }, 5000); // Hide message after 5 seconds
        }
    } else {
        console.warn('Status message div not found. Message:', message);
    }
}

// Modified deleteEmergencies to redirect to the new confirmation page
function deleteEmergencies() {
    // Redirect to the new confirmation page
    window.location.href = '/confirm_ndrf_delete';
}

// Call on load and every 2 seconds
loadEmergencies();
setInterval(loadEmergencies, 2000);
setTimeout(() => map.invalidateSize(), 100);

// Check for success message from redirect
window.onload = function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('status') === 'deleted') {
        displayMessage("✅ All emergencies deleted successfully!", 'success');
        // Clean the URL to remove the query parameter
        window.history.replaceState({}, document.title, window.location.pathname);
    }
};
