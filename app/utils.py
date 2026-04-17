import geojson
from geojson import Feature, FeatureCollection, LineString

def gpx_to_geojson(gpx):
    """Преобразует объект gpxpy в GeoJSON FeatureCollection с треками."""
    features = []
    for track in gpx.tracks:
        for segment in track.segments:
            coords = [(point.longitude, point.latitude) for point in segment.points]
            if len(coords) >= 2:
                line = LineString(coords)
                features.append(Feature(geometry=line, properties={"name": track.name}))
    return FeatureCollection(features)