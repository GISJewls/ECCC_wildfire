#----------------------------------------------------------------------------------
#                            Wildfire Occurence
#----------------------------------------------------------------------------------
# SCRIPT NAME:  wildfire_occurence.py
#               v.2026.0323
#
# PURPOSE:      Calculate wildfire occurence over a time range
#
# ARGUMENTS:    name        Type    Input Description
#              --------------------------------------------------------------------
#               src_fire    <R>     Soucre wildfire raster
#               src_aoi     <R>     Area of interest (herd boundaries)
#               src_aoi_fld <R>     Unique field from aoi
#               minYear     <R>     Minimum year
#               maxYear     <R>     Maximum year
#               tblExport   <R>     Export table name and location
#
# OUTPUTS:      combines annual wildfire intensity with annual wildfire rasters
#
# AUTHOR:       Julie Duval, fRI Research
#
# CREATED ON:   March 11, 2026
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
    error('Problem opening or writing to the wildfire_occurence_log.txt file')

#----------------------------------------------------------------------------------
# Fire Metrics
#==================================================================================
def WildfireOccurence(args):
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
            minYear = arcpy.GetParameterAsText(3)
            maxYear = arcpy.GetParameterAsText(4)
            tblExport = arcpy.GetParameterAsText(5)

            display('\nWildfire raster:         ' + src_fire +
                    '\nArea of interest:        ' + src_aoi +
                    '\nArea of interest field:  ' + src_aoi_fld +
                    '\nMinimum Year:            ' + minYear +
                    '\nMaximum Year:            ' + maxYear +
                    '\nExport table:            ' + tblExport +
                    '\n\n', log)

            #==================================================================
            # Processing Environment
            #------------------------------------------------------------------
            arcpy.env.extent = src_aoi
            arcpy.env.snapRaster = src_fire
            arcpy.env.cellSize = src_fire

            #==================================================================
            # ANALYSIS
            #==================================================================
            # -----------------------------------------------------------------
            # Step 1: combine intensity rasters to determine which cells were
            #         identified as salvaged, while retaining the intensity
            # -----------------------------------------------------------------
            display(' ... Creating binary raster where year >= ' + minYear +
                    ' and year <= ' + maxYear, log)

            # create binary raster
            expr = 'Value >= ' + minYear + ' and Value <= ' + maxYear
            binaryRst = arcpy.sa.Con(arcpy.Raster(src_fire), 1, 0, expr)

            display(' ... Converting aoi polygons to raster', log)
            aoiRst = r'memory\aoiRst'
            outTbl = r'memory\tempTable'

            arcpy.conversion.FeatureToRaster(
                in_features  = src_aoi,
                field = src_aoi_fld,
                out_raster = aoiRst,
                cell_size = arcpy.env.cellSize
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
              '\nError Info:    ' + str(sys.exc_info()[1]), log)
        log.close()


if __name__ == '__main__':
    WildfireOccurence(sys.argv)
