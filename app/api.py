from flask import Blueprint, request, jsonify, current_app
from app.models import Marker, GPXTrack
import requests

api_bp = Blueprint('api', __name__)

@api_bp.route('/markers')
def get_markers():
    markers = Marker.query.filter_by(is_public=True).all()
    features = []
    for marker in markers:
        features.append({
            "type": "Feature",
            "id": marker.id,
            "geometry": {
                "type": "Point",
                "coordinates": [marker.longitude, marker.latitude]
            },
            "properties": {
                "balloonContent": f"<h3>{marker.title}</h3><p>{marker.description}</p>",
                "clusterCaption": marker.title,
                "hintContent": marker.title
            }
        })
    return jsonify({"type": "FeatureCollection", "features": features})

@api_bp.route('/weather')
def get_weather():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"error": "Missing coordinates"}), 400
    
    url = f"https://api.weather.yandex.ru/v2/forecast?lat={lat}&lon={lon}"
    headers = {"X-Yandex-API-Key": current_app.config['YANDEX_WEATHER_KEY']}
    
    response = requests.get(url, headers=headers)
    # Возвращаем только фактическую погоду для простоты
    if response.status_code == 200:
        data = response.json()
        return jsonify(data.get('fact', {}))
    else:
        return jsonify({"error": "Weather API error"}), response.status_code

@api_bp.route('/tracks')
def get_tracks():
    tracks = GPXTrack.query.all()
    result = []
    for track in tracks:
        if track.geojson_data:
            result.append({
                "id": track.id,
                "filename": track.filename,
                "geojson": track.geojson_data
            })
    return jsonify(result)