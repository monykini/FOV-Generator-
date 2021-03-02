from .Shapes import Hexa , Point , userMarker , FOV
from .Grid import hexaGrid
from .Tiles import tileGatherer


class FOV_fucade():
    """
    docstring
    """
    def create_FOV(self,latlon,size):
        Marker = userMarker(latlon,size)
        Marker.get_square()
        Grid = hexaGrid(Marker)
        area_array = tileGatherer(Marker)
        area_array.conver_raster_tiles()
        Grid.Mapper(area_array.areaArray)  
        return Grid.hexas , Marker.get_square_4326(),area_array.areaArray,Grid.flat_surfaces


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
