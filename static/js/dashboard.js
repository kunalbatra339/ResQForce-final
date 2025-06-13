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
                    return;
                }

                const emergencies = await response.json();
                console.log('[DEBUG] Emergency Data:', emergencies);

                if (emergencies.length === 0) {
                    console.warn('No emergencies found');
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
            } catch (error) {
                console.error('Critical Error:', error);
            }
        }

        // Call on load and every 2 seconds
        loadEmergencies();
        setInterval(loadEmergencies, 2000);
        setTimeout(() => map.invalidateSize(), 100);

        // New function to delete all emergencies
        async function deleteEmergencies() {
            if (!confirm("Are you sure you want to delete ALL emergencies?")) return;

            try {
                const response = await fetch('/api/delete_emergencies', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const result = await response.json();
                if (response.ok) {
                    alert("✅ All emergencies deleted successfully!");
                    loadEmergencies();
                } else {
                    alert("❌ Error: " + result.error);
                }
            } catch (err) {
                console.error(err);
                alert("⚠ Something went wrong.");
            }
        }
