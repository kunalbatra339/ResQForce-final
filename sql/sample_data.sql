
INSERT INTO agencies (name, email, password, expertise, latitude, longitude, last_updated, role, verified, agency_type)
VALUES 
('Rapid Response', 'rapid@example.com', 'hashed_password1', 'Fire', 28.6139, 77.2090, NOW(), 'agency', TRUE, 'state'),
('Disaster Aid', 'aid@example.com', 'hashed_password2', 'Flood', 19.0760, 72.8777, NOW(), 'agency', FALSE, 'local'),
('NDRF Central', 'ndrf@example.com', 'hashed_password3', 'All Hazards', 22.5726, 88.3639, NOW(), 'ndrf', TRUE, 'central');


INSERT INTO emergencies (latitude, longitude, description, status, created_at, reported_by, tag)
VALUES
(28.7041, 77.1025, 'Major fire outbreak in industrial area', 'pending', NOW(), 'public', 'fire'),
(19.2183, 72.9781, 'Flooded residential zone, immediate help needed', 'pending', NOW(), 'public', 'flood'),
(13.0827, 80.2707, 'Multi-vehicle accident on highway', 'pending', NOW(), 'agency', 'accident');


INSERT INTO resources (agency_id, name, quantity)
VALUES 
(1, 'Fire Trucks', 5),
(2, 'Boats', 3),
(3, 'Medical Kits', 10);