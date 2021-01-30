from .Shapes import Hexa , Point , userMarker , FOV
from .Grid import hexaGrid
from .Tiles import tileGatherer


class FOV_fucade():
    """
    docstring
    """
    def create_FOV(self,latlon):
        Marker = userMarker(latlon,200)
        Marker.get_square()
        Grid = hexaGrid(Marker)
        Grid.calculate_grid()
        area_array = tileGatherer(Marker)
        area_array.conver_raster_tiles()
        Grid.Mapper(area_array.areaArray)

        return Grid.hexas , Marker.get_square_4326()


    def get_ti(self,latlon):
        Marker = userMarker(latlon,200)
        Marker.get_square()
        area_array = tileGatherer(Marker)
        area_array.conver_raster_tiles()
        return area_array.areaArray


    def test_fov(self):
        fov = FOV()
        fov.create_fov([0,10],[10,0])
        print(fov.view_area)

# def main():
#     area  = FOV_fucade()
#     area.create_FOV()
# #     hexagons = area.create_hexagons()
# # #   print(hexagons.to_string())
# #     hexagons = area.get_flat_surfaces(hexagons)

# if __name__ == "__main__":
#     main()