import math
from shapely.geometry import Point, Polygon, LineString
from .Shapes import Hexa , Points , userMarker

class hexaGrid():
    """
    creates a hexagrid \n
    hexaGrid(userMarker)
    methods: \n
    calculate_grid(self) :- creates a hexagrid
    Mapper(self,tilesArray) :- takes tilesArray form tile_gather class and maps each point to respective hexa in grid
    """
    def __init__(self,userMarker):
        self.hexas = []
        self.userMarker = userMarker
        self.sideLength = 28.868

    def calculate_grid(self):
        """
        returns an array of Points describing hexagons centers that are inside the given bounding_box \n
        :return: The hexagon grid \n
        """
        grid = []

        v_step = math.sqrt(3) * self.sideLength
        h_step = 1.5 * self.sideLength

        x_min = self.userMarker.square[3][0]
        x_max = self.userMarker.square[1][0]
        y_min = self.userMarker.square[1][1]
        y_max = self.userMarker.square[3][1]
        # print(x_min , x_max , y_max , y_min)

        h_skip = math.ceil(x_min / h_step) - 1
        h_start = h_skip * h_step

        v_skip = math.ceil(y_min / v_step) - 1
        v_start = v_skip * v_step

        h_end = x_max + h_step
        v_end = y_max + v_step

        if v_start - (v_step / 2.0) < y_min:
                v_start_array = [v_start + (v_step / 2.0), v_start]
        else:
                v_start_array = [v_start - (v_step / 2.0), v_start]

        v_start_idx = int(abs(h_skip) % 2)

        c_x = h_start
        c_y = v_start_array[v_start_idx]
        v_start_idx = (v_start_idx + 1) % 2
        # transformer = Transformer.from_crs("epsg:3857", "epsg:4326")
        while c_x < h_end:
                while c_y < v_end:
                        # c_x1, c_y1=transformer.transform(c_x, c_y)
                        hexa = Hexa([c_x, c_y])
                        grid.append(hexa)
                        c_y += v_step
                c_x += h_step
                c_y = v_start_array[v_start_idx]
                v_start_idx = (v_start_idx + 1) % 2
        self.hexas = grid
        return grid

    def Mapper(self,tilesArray):
        temp=[]
        for data in tilesArray:
            for hexa in self.hexas:
                # print(hexa.create_hexagon())
                if Point(data.mac_latlon[0],data.mac_latlon[1]).within(hexa.create_hexagon()):
                        hexa.points.append(data)
                        # print(data)
            
        return temp