from Shapes import Hexa , Point , userMarker
from Grid import hexaGrid
from Tiles import tileGatherer


class FOV_fucade():
    """
    docstring
    """
    def create_FOV(self):
        Marker = userMarker([33.64013671875,73.0455032],200)
        Marker.get_square()
        Grid = hexaGrid(Marker)
        Grid.calculate_grid()
        print(Grid.hexas[10].create_hexagon())
        # print(Grid.hexas[1].get_sides_4326())
        # print(len(Grid.hexas))
        # Grid.hexas[10].check_flatness()
        print(Grid.hexas[10].triangles)
        area_array = tileGatherer(Marker)
        area_array.conver_raster_tiles()
        Grid.Mapper(area_array.areaArray)
        print(Grid.hexas[10].points)
        print(Grid.hexas[10].check_flatness()) 


        


def main():
    area  = FOV_fucade()
    area.create_FOV()
#     hexagons = area.create_hexagons()
# #   print(hexagons.to_string())
#     hexagons = area.get_flat_surfaces(hexagons)

if __name__ == "__main__":
    main()