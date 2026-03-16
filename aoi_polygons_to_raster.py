#----------------------------------------------------------------------------------
#              Wildfire Metrics: Convert AOI polygon to raster
#----------------------------------------------------------------------------------
# SCRIPT NAME:  aoi_polygon_to_raster.py
#               v.2026.0311
#
# PURPOSE:      Create herd range rasters from polygons and calculate raster
#               areas.
#
# ARGUMENTS:    name        Type    Input Description
#              --------------------------------------------------------------------
#               aoi         <R>     Area of interest (herd boundaries)
#               aoi_fld     <R>     Unique field from aoi
#               outWksp     <R>     Output workspace
#               snapRst     <O>     Snap raster
#               outCellSize <R>     Output raster cell size, default = 30m
#
# OUTPUTS:      summary table with area
#
# AUTHOR:       Julie Duval, fRI Research
#
# CREATED ON:   March 10th, 2026
#
# EDITORS:      Julie Duval, fRI Research
#
# LAST UPDATES: March 10, 2026
#
# NOTES:        tested with ArcGIS PRO 3.6.2
#               requires Advanced licensing with Spatial Analyst extension
#
#==================================================================================
# Import libraries
import sys, os
import datetime
import traceback
import arcpy
from arcpy import env
from os.path import join as fp
from CheckLicenses import CheckArcInfo, CheckSpatialExt
from functions import isNameOk, isPathOk, display, error, warning

class exitError(Exception):
    pass

#==================================================================================
# Set Global Variables tool paths
#----------------------------------------------------------------------------------
global log

#==================================================================================
# Set up file to save display log for user
#----------------------------------------------------------------------------------
try:
    fpath = os.path.split(sys.path[0])[0]
    starttime = datetime.datetime.now()
    logFile = fp(fpath, 'aoi_polygon_to_raster_log.txt')
    log = open(logFile, 'a')
    log.write('\n\n' + '=' * 89 + '\nTool Started on: ' +
                str(starttime.strftime('%d-%b-%Y %I:%M %p')) + '\n')
except:
    error('Problem opening or writing to the polymetrics_log.txt file')

#----------------------------------------------------------------------------------
# Fire Metrics
#==================================================================================
def HerdPolygons(args):
    try:
        # Only proceed if the required ArcGIS licenses are available
        if CheckArcInfo() == "yes" and CheckSpatialExt() == "yes":

            #======================================================================
            # Read user-defined parameters
            # ---------------------------------------------------------------------
            display('\n ... Reading user inputs', log)

            # inputs
            aoi = arcpy.GetParameterAsText(0)
            aoi_fld = arcpy.GetParameterAsText(1)
            snapRst = arcpy.GetParameterAsText(2)
            tblExport = arcpy.GetParameterAsText(3)

            #======================================================================
            # Processing Environment
            #----------------------------------------------------------------------
            arcpy.env.extent = aoi
            arcpy.env.mask = aoi
            arcpy.env.snapRaster = snapRst
            arcpy.env.cellSize = snapRst

            #======================================================================
            # ANALYSIS
            #======================================================================

            # -----------------------------------------------------------------
            # Step 1: Create raster from polygons
            # -----------------------------------------------------------------
            display(' ... Converting polygons to raster', log)
            outRst = r'memory\outRst'

            arcpy.conversion.PolygonToRaster(
                in_features = aoi,
                value_field = aoi_fld,
                out_rasterdataset = outRst,
                cell_assignment = 'MAXIMUM_COMBINED_AREA'
            )

            display(' ... Adding fields to output table', log)
            expr = '!Count! * 0.0009'
            arcpy.management.AddField(
                in_table = outRst,
                field_name = 'RST_AREA_KM2',
                field_type = 'DOUBLE',
            )
            arcpy.management.CalculateField(
                in_table = outRst,
                field = 'RST_AREA_KM2',
                expression = expr
            )

            # -----------------------------------------------------------------
            # Step 2: Export raster to csv
            # -----------------------------------------------------------------
            display(' ... Exporting raster attributes to csv')
            arcpy.conversion.ExportTable(
                in_table = outRst,
                out_table = tblExport
            )

##            # -----------------------------------------------------------------
##            # Step 2: Export polygon FC to csv
##            # -----------------------------------------------------------------
##            display('     - Exporting raster attributes to csv')
##            arcpy.conversion.ExportTable(
##                in_table = aoi,
##                out_table = aoiExport
##            )

            log.close()

    except:
        tbinfo = traceback.format_tb(sys.exc_info()[2])[0]
        error('\nPYTHON ERRORS in main():'
              '\nTraceback Info:    ' + tbinfo +
              '\nError Type:    ' + str(sys.exc_info()[0]) +
              '\nError Info:    ' + str(sys.exc_info()[1]))
        log.close()

        # release data in memory
        memList = [r'memory\outRst']
        for mem in memList:
            if arcpy.Exists(mem): arcpy.management.Delete(mem)


if __name__ == '__main__':
    HerdPolygons(sys.argv)
