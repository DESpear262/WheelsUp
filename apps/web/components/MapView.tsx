/**
 * MapView Component
 *
 * Displays a Mapbox map with flight school location markers.
 * Shows campus location with interactive map controls.
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MapPin, Navigation, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

// Set Mapbox access token
if (typeof window !== 'undefined') {
  mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN || '';
}

interface MapViewProps {
  latitude: number;
  longitude: number;
  schoolName: string;
  address?: string;
  city?: string;
  state?: string;
  zoom?: number;
  className?: string;
}

export default function MapView({
  latitude,
  longitude,
  schoolName,
  address,
  city,
  state,
  zoom = 13,
  className = ''
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    try {
      // Initialize map
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [longitude, latitude],
        zoom: zoom,
        attributionControl: false,
        logoPosition: 'bottom-right'
      });

      // Add navigation controls
      map.current.addControl(
        new mapboxgl.NavigationControl({
          showCompass: false,
          showZoom: true
        }),
        'top-right'
      );

      // Add geolocate control
      map.current.addControl(
        new mapboxgl.GeolocateControl({
          positionOptions: {
            enableHighAccuracy: true
          },
          trackUserLocation: false,
          showUserHeading: false
        }),
        'top-right'
      );

      // Wait for map to load
      map.current.on('load', () => {
        setMapLoaded(true);
        setIsLoading(false);

        if (!map.current) return;

        // Add marker for school location
        const markerElement = document.createElement('div');
        markerElement.className = 'school-marker';
        markerElement.innerHTML = `
          <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center shadow-lg border-2 border-white">
            <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
            </svg>
          </div>
        `;

        new mapboxgl.Marker(markerElement)
          .setLngLat([longitude, latitude])
          .setPopup(
            new mapboxgl.Popup({ offset: 25 })
              .setHTML(`
                <div class="p-2">
                  <h3 class="font-semibold text-gray-900">${schoolName}</h3>
                  ${address ? `<p class="text-sm text-gray-600">${address}</p>` : ''}
                  ${city && state ? `<p class="text-sm text-gray-600">${city}, ${state}</p>` : ''}
                </div>
              `)
          )
          .addTo(map.current);

        // Add a circle to show approximate area
        map.current.addSource('school-radius', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: [{
              type: 'Feature',
              geometry: {
                type: 'Point',
                coordinates: [longitude, latitude]
              },
              properties: {}
            }]
          }
        });

        map.current.addLayer({
          id: 'school-radius-fill',
          type: 'circle',
          source: 'school-radius',
          paint: {
            'circle-radius': 50,
            'circle-color': '#3B82F6',
            'circle-opacity': 0.1,
            'circle-stroke-color': '#3B82F6',
            'circle-stroke-width': 2,
            'circle-stroke-opacity': 0.3
          }
        });
      });

      // Handle map errors
      map.current.on('error', (e) => {
        console.error('Mapbox error:', e);
        setError('Failed to load map');
        setIsLoading(false);
      });

    } catch (err) {
      console.error('Failed to initialize map:', err);
      setError('Failed to initialize map');
      setIsLoading(false);
    }

    // Cleanup function
    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [latitude, longitude, zoom, schoolName, address, city, state]);

  // Reset map view to school location
  const resetView = () => {
    if (map.current) {
      map.current.flyTo({
        center: [longitude, latitude],
        zoom: zoom,
        duration: 1000
      });
    }
  };

  // Get directions (opens in external maps app)
  const getDirections = () => {
    const mapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`;
    window.open(mapsUrl, '_blank');
  };

  if (error) {
    return (
      <div className={`bg-gray-100 rounded-lg flex items-center justify-center ${className}`}>
        <div className="text-center p-6">
          <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Map Unavailable</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={getDirections}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Navigation className="w-4 h-4 mr-2" />
            Get Directions
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Loading state */}
      {isLoading && (
        <div className="absolute inset-0 bg-gray-100 rounded-lg flex items-center justify-center z-10">
          <div className="text-center">
            <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">Loading map...</p>
          </div>
        </div>
      )}

      {/* Map container */}
      <div
        ref={mapContainer}
        className="w-full h-96 rounded-lg"
        style={{ minHeight: '400px' }}
      />

      {/* Custom controls overlay */}
      {mapLoaded && (
        <div className="absolute top-4 left-4 flex flex-col space-y-2">
          <button
            onClick={resetView}
            className="p-2 bg-white rounded-md shadow-md hover:shadow-lg transition-shadow border border-gray-200"
            title="Reset view"
          >
            <RotateCcw className="w-4 h-4 text-gray-600" />
          </button>

          <button
            onClick={getDirections}
            className="p-2 bg-white rounded-md shadow-md hover:shadow-lg transition-shadow border border-gray-200"
            title="Get directions"
          >
            <Navigation className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      )}

      {/* Location info overlay */}
      <div className="absolute bottom-4 left-4 right-4 bg-white rounded-lg shadow-md border border-gray-200 p-4">
        <div className="flex items-start space-x-3">
          <MapPin className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-gray-900 truncate">{schoolName}</h4>
            {address && (
              <p className="text-sm text-gray-600 truncate">{address}</p>
            )}
            {(city || state) && (
              <p className="text-sm text-gray-600">
                {[city, state].filter(Boolean).join(', ')}
              </p>
            )}
            <div className="mt-2 flex items-center text-xs text-gray-500">
              <span>{latitude.toFixed(6)}, {longitude.toFixed(6)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
