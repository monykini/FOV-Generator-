from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from generator.models import buildingData

buildingdata_mapping = {
    'height': 'Height',
    'geom': 'MULTIPOLYGON',
}


world_shp = f'buidlingsData/newyork/bldg_footprints.shp'

def run(verbose=True):
    lm = LayerMapping(buildingData, str(world_shp),buildingdata_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)