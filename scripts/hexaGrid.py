import math
from shapely.geometry import Point, Polygon, LineString
from FOV.settings import Islamabad_bbox
from pyproj import Transformer
from generator.models import modelHexaGrid,cities
from django.contrib.gis import geos


def calculate_grid(xmin,ymin,xmax,ymax):
        """
        returns an array of Points describing hexagons centers that are inside the given bounding_box \n
        :return: The hexagon grid \n
        """
        grid = []

        v_step = math.sqrt(3) * 28.868
        h_step = 1.5 * 28.868

        print(v_step,h_step,'#step')

        x_min = xmin   
        x_max = xmax
        y_min = ymin
        y_max = ymax

        print(x_min , x_max , y_max , y_min)

        h_skip = math.ceil(x_min / h_step) - 1
        h_start = h_skip * h_step

        v_skip = math.ceil(y_min / v_step) - 1
        v_start = v_skip * v_step

        h_end = x_max + h_step
        v_end = y_max + v_step

        print(h_end,v_end,h_start,v_start,h_skip,v_skip)

        if v_start - (v_step / 2.0) < y_min:
                v_start_array = [v_start + (v_step / 2.0), v_start]
        else:
                v_start_array = [v_start - (v_step / 2.0), v_start]

        v_start_idx = int(abs(h_skip) % 2)

        c_x = h_start
        c_y = v_start_array[v_start_idx]
        v_start_idx = (v_start_idx + 1) % 2
        transformer = Transformer.from_crs("epsg:3857", "epsg:4326")
        x = 0
        while c_x < h_end:
                y = 0
                while c_y < v_end:
                        c_x1, c_y1=transformer.transform(c_x, c_y)
                        hexa = [Point([c_y, c_x]),Point([c_y1, c_x1]),x,y]
                        grid.append(hexa)
                        c_y += v_step
                        y+=1
                c_x += h_step
                c_y = v_start_array[v_start_idx]
                v_start_idx = (v_start_idx + 1) % 2
                x+=1
        return grid

def create_hexagon(point):
    """
    Create a hexagon centered on (x, y)
    :param l: length of the hexagon's edge
    :param x: x-coordinate of the hexagon's center
    :param y: y-coordinate of the hexagon's center
    :return: The polygon containing the hexagon's coordinates
    """
    c = [[point.y + math.cos(math.radians(angle)) * 28.868, point.x + math.sin(math.radians(angle)) * 28.868] for angle in range(0, 360, 60)]
    sides = Polygon(c)
    return sides

def get_sides_4326(sides):
        transformer = Transformer.from_crs("epsg:3857" , "epsg:4326")
        polygon_4326 = []
        for p in list(sides.exterior.coords):
            x,y = transformer.transform(p[0], p[1])
            polygon_4326.append([y,x])
        return Polygon(polygon_4326)

def run(verbose=True):
    transformer = Transformer.from_crs("epsg:4326","epsg:3857")
    xmin,ymin=transformer.transform(Islamabad_bbox['min_lon'],Islamabad_bbox['min_lat'])
    xmax,ymax=transformer.transform(Islamabad_bbox['max_lon'],Islamabad_bbox['max_lat'])
    transformer = Transformer.from_crs("epsg:3857","epsg:4326")
    print(transformer.transform(ymin, xmin))
    print(transformer.transform(ymax, xmax))
    print(xmin,ymin,xmax,ymax)
    hexas = calculate_grid(xmin,ymin,xmax,ymax)
    city = cities.objects.create(name = 'islamabad')
    for hexa in hexas:
        macsides = create_hexagon(hexa[0])
        ws48sides = get_sides_4326(macsides)
        center48 = geos.Point(hexa[1].x,hexa[1].y)
        centermac = geos.Point(hexa[0].x,hexa[0].y)
        polygonmac = geos.Polygon(tuple(macsides.exterior.coords))
        wsg48polygon = geos.Polygon(tuple(ws48sides.exterior.coords))
        hexa = modelHexaGrid(wsg48polygon=wsg48polygon , wsg48center = center48,macpolygon = polygonmac , mac48center =centermac,city= city)
        hexa.save()
