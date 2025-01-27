import requests
import Maxar_OGC.process as process
from pathlib import Path


class WCS:
    def __init__(self, session):
        self.base_url = session['base_url'] + "deliveryservice/wcsaccess"
        self.headers = session['headers']
        self.connect_id = session['connectid']
        self.response = None
        self.version = session['version']
        self.querystring = self._init_querystring()

    def return_image(self, bbox, identifier, gridoffsets, srsname="EPSG:4326", **kwargs):
        """
        Function finds the imagery matching a bbox or feature id
        Kwargs:
            bbox = String bounding box of AOI. Comma delimited set of coordinates. (miny,minx,maxy,maxx)
            filter = CQL filter used to refine data of search.
            gridcrs = String of the Coordinate reference system used. Crs is EPSG:4326.
            gridoffsets = Integer value representing the vertical number of pixels to return
            identifier = String of the feature id to be returned.
            format = String of the format of the response image either jpeg, png or geotiff
            featureprofile = String of the desired stacking profile. Defaults to account Default
            srsname (string) = Desired projection. Defaults to EPSG:4326
        Returns:
            requests response object of desired image
        """

        self.querystring = self._init_querystring()
        keys = list(kwargs.keys())
        process._validate_bbox(bbox, srsname=srsname)
        if 'filter' in kwargs:
            process.cql_checker(kwargs.get('filter'))
        self.querystring.update({'boundingbox': bbox})
        self.querystring.update({'identifier': identifier})
        self.querystring.update({'gridoffsets': gridoffsets})
        if srsname != "EPSG:4326":
            self.querystring['gridcrs'] = "urn:ogc:def:crs:EPSG::{}".format(srsname[5:])
            self.querystring.update({'gridbasecrs': 'urn:ogc:def:crs:EPSG::{}'.format(srsname[5:])})
            bbox_list = [i for i in bbox.split(',')]
            bbox = ",".join([bbox_list[1], bbox_list[0], bbox_list[3], bbox_list[2], srsname])
            self.querystring.update({'boundingbox': bbox})
        if 'filter' in keys:
            self.querystring.update({'coverage_cql_filter': kwargs['filter']})
            del (kwargs['filter'])
        for key, value in kwargs.items():
            if key in self.querystring.keys():
                self.querystring[key] = value
            else:
                self.querystring.update({key: value})
        request = requests.get(self.base_url, headers=self.headers, params=self.querystring)
        self.response = request
        return process._response_handler(self.response)

    def _init_querystring(self):
        querystring = {'connectid': self.connect_id,
                       'service': 'WCS',
                       'request': 'GetCoverage',
                       'version': '1.3.0',
                       'gridcrs': 'urn:ogc:def:crs:EPSG::4326',
                       'format': 'image/jpeg',
                       'SDKversion': '{}'.format(self.version)
                       }
        return querystring

    def parse_coverage(self, coverage):
        writelist = []
        filename = Path(coverage)
        filename_replace_ext = filename.with_suffix('.txt')
        with open(coverage, 'rb') as open_file:
            for line in open_file:
                writelist.append(line)
        writelist1 = writelist[:21]
        writelist2 = writelist[21:]
        with open(filename_replace_ext, 'wb') as write_file:
            for item in writelist1:
                write_file.write(item)
        with open(coverage, 'wb') as write_file:
            for item in writelist2:
                write_file.write(item)
        return (str(filename_replace_ext) + " and " + str(coverage) + " have been downloaded")
