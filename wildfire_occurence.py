#----------------------------------------------------------------------------------
#                            Wildfire Occurence
#----------------------------------------------------------------------------------
# SCRIPT NAME:  wildfire_occurence.py
#               v.2026.0311
#
# PURPOSE:      Calculate wildfire occurence over a time range
#
# ARGUMENTS:    name        Type    Input Description
#              --------------------------------------------------------------------
#               aoi         <R>     Area of interest (herd boundaries)
#               aoi_fld     <R>     Unique field from aoi
#               wildfires   <R>     Annual wildfire data, polygons
#               wfYear      <R>     Wildfire year, integer
#               wfPrefix    <R>     Prefix used for outputs, string
#               outWksp     <R>     Output workspace
#               snapRst     <O>     Snap raster
#               outCellSize <R>     Output raster cell size, default = 30m
#
# OUTPUTS:      combines annual wildfire intensity with annual wildfire rasters
#
# AUTHOR:       Julie Duval, fRI Research
#
# CREATED ON:   March 11, 2026
#
# EDITORS:      Julie Duval, fRI Research
#
# LAST UPDATES:
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
    logFile = fp(fpath, 'wildfire_occurence_log.txt')
    log = open(logFile, 'a')
    log.write('\n\n' + '=' * 89 + '\nTool Started on: ' +
                str(starttime.strftime('%d-%b-%Y %I:%M %p')) + '\n')
except:
    error('Problem opening or writing to the polymetrics_log.txt file')

#----------------------------------------------------------------------------------
# Fire Metrics
#==================================================================================
def CombineRasters(args):
    try:
        # Only proceed if the required ArcGIS licenses are available
        if CheckArcInfo() == "yes" and CheckSpatialExt() == "yes":

            #======================================================================
            # Read user-defined parameters
            # ---------------------------------------------------------------------
            display(' ... Reading user inputs', log)

            # inputs
            src_fire = arcpy.GetParameterAsText(0)
            src_aoi = arcpy.GetParameterAsText(1)
            src_aoi_fld = arcpy.GetParameterAsText(2)
            snapRst = arcpy.GetParameterAsText(3)
            minYear = arcpy.GetParameterAsText(4)
            maxYear = arcpy.GetParameterAsText(5)
            tblExport = arcpy.GetParameterAsText(6)

            #==================================================================
            # Processing Environment
            #------------------------------------------------------------------
            arcpy.env.extent = src_aoi
            arcpy.env.snapRaster = snapRst
            arcpy.env.cellSize = snapRst

            #==================================================================
            # ANALYSIS
            #==================================================================
            # -----------------------------------------------------------------
            # Step 1: combine intenstiy rasters to determine which cells were
            #         identified as salvaged, while retaining the intensity
            # -----------------------------------------------------------------
            display(' ... Creating binary raster', log)
            # create binary raster
            expr = 'Value >= ' + str(minYear) + 'and Value <= ' + str(maxYear)
            binaryRst = arcpy.sa.Con(arcpy.Raster(src_fire), 1, 0, expr)

            display(' ... Converting polygons to raster', log)
            aoiRst = r'memory\aoiRst'
            outTbl = r'memory\tempTable'

            arcpy.conversion.PolygonToRaster(
                in_features = src_aoi,
                value_field = src_aoi_fld,
                out_rasterdataset = aoiRst,
                cell_assignment = 'MAXIMUM_COMBINED_AREA'
            )

            display(' ... Analysing zonal statistics', log)
            arcpy.sa.ZonalStatisticsAsTable(
                in_zone_data = aoiRst,
                zone_field = src_aoi_fld,
                in_value_raster = binaryRst,
                out_table = outTbl,
                ignore_nodata = 'DATA',
                statistics_type = 'SUM'
            )

            arcpy.conversion.ExportTable(
                in_table = outTbl,
                out_table = tblExport
            )

            # close log file
            log.close()

            # delete temporary rasters
            for rst in [aoiRst]:
                if arcpy.Exists(rst): arcpy.management.Delete(rst)

    except:
        tbinfo = traceback.format_tb(sys.exc_info()[2])[0]
        error('\nPYTHON ERRORS in CombineRasters():'
              '\nTraceback Info:    ' + tbinfo +
              '\nError Type:    ' + str(sys.exc_info()[0]) +
              '\nError Info:    ' + str(sys.exc_info()[1]))
        log.close()


if __name__ == '__main__':
    CombineRasters(sys.argv)
