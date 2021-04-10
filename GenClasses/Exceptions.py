
class Error(Exception):
    pass

class WaterTile(Error):
    pass

class NoDataAvailable(Error):
    pass

class NotEnoughPoints(Error):
    pass