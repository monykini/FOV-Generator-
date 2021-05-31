import tensorflow as tf
from tensorflow import keras
import numpy as np
import io
import matplotlib.pyplot as plt
from PIL import Image
from numpy import asarray
import requests
import mercantile
from django.contrib.gis import geos
import rasterio
import shapely

_GLOBAL_MIN = np.array([1.0, 1.0, 23.0])
_GLOBAL_MAX = np.array([1933.0, 2047.0, 1610.0])
IMAGE_HEIGHT, IMAGE_WIDTH = 650, 650


model = keras.models.load_model('CompleteSaves')


def _load_tif(filename: str,max_per_channel: np.ndarray,min_per_channel: np.ndarray) -> np.ndarray:
  with tf.io.gfile.GFile(filename, "rb") as fid:
    img = tfds.core.lazy_imports.skimage.external.tifffile.imread(
        io.BytesIO(fid.read())).astype(np.float32)
  img = (img - min_per_channel) / (max_per_channel - min_per_channel) * 255
  img = np.clip(img, 0, 255).astype(np.uint8)
  return img

def adjust_contrast_and_normalize_prod(img):
    image = img
    image = tf.cast(image, tf.float32) / 255.0
    image = tf.image.resize(image, (448, 448))
    return image

def get_tiles_ML(square_4326,PixelXYToLatLongOSM):
        tiles = []
        for p in square_4326:
                mercent = mercantile.tile(p[1],p[0],18)
                tiles.append([mercent.x,mercent.y])

        x_matrix =  [ p[1] for p in tiles ]
        y_matrix = [p[0] for p in tiles]
        
        x_matrix_max , x_matrix_min = max(x_matrix) , min(x_matrix)
        y_matrix_max , y_matrix_min = max(y_matrix) , min(y_matrix)
        print(x_matrix_max , x_matrix_min)
        total_x_axis_tiles = x_matrix_max-x_matrix_min+1
        total_y_axis_tiles = y_matrix_max-y_matrix_min+1

        top_left_tile = tiles[0]
        total_tiles_matrix=[]
        for x in range(total_x_axis_tiles):
                temp=[]
                for y in range(total_y_axis_tiles):
                        temp.append([top_left_tile[0]-y,top_left_tile[1]+x])
                total_tiles_matrix.append(temp)

        total_tiles_matrix = total_tiles_matrix[::-1]

        polygons = []
        for i in total_tiles_matrix:
            for j in i:
                polys = get_pred(j[0],j[1],PixelXYToLatLongOSM)
                polygons.extend(polys)
        
        return polygons



def get_pred(x,y,PixelXYToLatLongOSM):
        img = Image.open(requests.get(f'https://api.mapbox.com/v4/mapbox.satellite/18/{x}/{y}@2x.png?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ', stream=True).raw)
        im1 = img.save(f"{x},{y}.png")
        img = asarray(img)
        print(img.shape,"shape")
        img = adjust_contrast_and_normalize_prod(img)
        img = np.expand_dims(img, axis=0)

        img = model.predict(img)
        
        img = tf.squeeze(img[0, :, :, 1]  > 0.4).numpy()

        plotimgs = Image.fromarray(img)
        plotimgs = plotimgs.resize((512, 512))
        plotimgs.save(f"{x},{y} pred.png")

        img = np.array(plotimgs).astype(np.uint8)

        sieved = rasterio.features.sieve(img, 10, out=np.zeros(img.shape, img.dtype),connectivity = 8)
        shapes = rasterio.features.shapes(sieved)

        polygons = [shapely.geometry.Polygon(shape[0]["coordinates"][0]) for shape in shapes if shape[1] == 1]

        # print(polygons)
        polygons = get_polygons(polygons,x,y,PixelXYToLatLongOSM)

        return polygons


def get_polygons(polygons,x,y,PixelXYToLatLongOSM):
        geos_polygons = []
        for p in polygons:
                latlons = []
                if p.area > 500:
                        for coords in p.exterior.coords:
                                y_pixal_world = (coords[1]+(512*y))
                                x_pixal_world = (coords[0]+(512*x))
                                lat , lon = PixelXYToLatLongOSM(x_pixal_world , y_pixal_world,18)
                                latlons.append((lon,lat))
                        geos_polygons.append(geos.Polygon(tuple(latlons)))

        return geos_polygons                
