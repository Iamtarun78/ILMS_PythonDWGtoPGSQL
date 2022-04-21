#!/usr/bin/python
import psycopg2
import arcgisscripting
import arcpy
import time
import os
import shutil
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
from collections import namedtuple

PORT_NUMBER = 8080
# This class will handles any incoming request


class handleRoutes(BaseHTTPRequestHandler):
  # Handler for the GET requests
  def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'json')
        self.end_headers()
  def do_POST(self):
	if(self.path == '/api'):
		self._set_headers()		
        content_len = int(self.headers.getheader('content-length', 0))
        post_body = self.rfile.read(content_len)
        dataVal=json.loads(post_body)
        fileParamVal=dataVal.get("file")
        typeParamVal=dataVal.get("type")
        arcpy.env.workspace = "C:/data"
        #Set local variables
        input_cad_dataset = "C:/data/"+fileParamVal+".DWG"
        timeVal = str(int(time.time()))
        fileName = fileParamVal+"_"+timeVal
        out_gdb_path = "C:/data/"+fileName+".gdb"
        sr=arcpy.SpatialReference("WGS 1984")
        out_dataset_name = fileName
        reference_scale = "1000"
        spatial_reference = "WGS 1984"
        #-Create a file geodatabase for the feature dataset
        arcpy.CreateFileGDB_management("C:/data", fileName+".gdb")
        #-Execute CreateFeaturedataset
        arcpy.CADToGeodatabase_conversion(input_cad_dataset, out_gdb_path,out_dataset_name, reference_scale)
        arcpy.env.workspace = "C:/data/"+fileName+".gdb"
        arcpy.FeatureClassToShapefile_conversion([typeParamVal], "C:/output")
        infc = r"C:/output/Polygon.shp"
        textPrj="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],\
              PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];\
              -400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119522E-09;\
              0.001;0.001;IsHighPrecision"
        sr = arcpy.SpatialReference("Geographic Coordinate Systems/World/WGS 1984")
        sr1 = arcpy.SpatialReference("Adindan UTM zone 37N")
        arcpy.DefineProjection_management(infc, sr1)
        outputSRS = 'Geographic Coordinate Systems/World/WGS 1984' # Geographic
        srOut = arcpy.SpatialReference(outputSRS)
        arcpy.Project_management(infc,"C:/output/Polygon_project.shp", srOut)
        cmd1 = 'shp2pgsql -I -s 4326 -W "latin1" C:\output\Polygon_project.shp tabletemp12| psql -d shapefile1 -U postgres'
        
        
        try:
            if os.system(cmd1) == 0:
                return self.sendResponse('{"message": "successfully data added in POSTGIS"}', 200, 'text/html')
                #shutil.rmtree('C:/output/')
                #os.mkdir("C:/output")
            else:
                print("Command failed to execute")
        
        except OSError as error:
            print(error)
            print("File descriptor is not associated with any terminal device")
		
        
  def do_GET(self):
    if (self.path == '/'):
		return self.sendResponse('{"hello": "world"}', 200, 'text/html')
		
  def sendResponse(self, res, status, type):
    self.send_response(status)
    self.send_header('Content-type', type)
    self.end_headers()
    # Send the html message
    self.wfile.write(res)
    return
	


try:
  # Create a web server and define the handler to manage the incoming requests
  server = HTTPServer(('', PORT_NUMBER), handleRoutes)
  print 'Started http server on port ' , PORT_NUMBER
  # Wait forever for incoming http requests
  server.serve_forever()

except KeyboardInterrupt:
  print '\nFarewell my friend.'
  server.socket.close()
