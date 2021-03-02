import json
import mercantile

def tileNumber(bbox):
    tiles = []
    square_4326 = bbox
    for p in square_4326:
        mercent = mercantile.tile(p[1],p[0],15)
        tiles.append([mercent.x,mercent.y])
    return tiles[0]


def jsonToFiles(city,filename):
    filepath = f'buidlingsData/{city}/{filename}'
    geoJsonFile = open(filepath, "r")
    geoJsonFile = geoJsonFile.read()
    geoJsonFile = json.loads(geoJsonFile)
    features = geoJsonFile['features']
    for f in features:
        if f['geometry']['type'] == "Polygon":
            bbox = f['geometry']['coordinates'][0]
        elif f['geometry']['type'] == "MultiPolygon":
            bbox = f['geometry']['coordinates'][0][0]
        tile = tileNumber(bbox)
        temp_filename = f'{tile[0]},{tile[1]}'
        tempFile = open(f'processedData/{city}/{temp_filename}.geojson', "a")
        data = {'cords':f['geometry']['coordinates'] 
        , 'height':f['properties']['Height']}
        tempFile.write(f"{data}\n")
        tempFile.close()
