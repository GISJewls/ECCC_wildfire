#----------------------------------------------------------------------------------
#            Wildfire Metrics: Area Burned and Annual Wildfire Rasters
#----------------------------------------------------------------------------------
# SCRIPT NAME:  wildfire_metrics_polygons.py
#               v.2026.0305
#
# PURPOSE:      Calculate wildfire metrics within defined caribou zones.
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
# OUTPUTS:      summary table and integer raster
#
# AUTHOR:       Julie Duval, fRI Research
#
# CREATED ON:   February 20th, 2026
#
# EDITORS:      Julie Duval, fRI Research
#
# LAST UPDATES: March 3, 2026
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
    logFile = fp(fpath, 'polymetrics_log.txt')
    log = open(logFile, 'a')
    log.write('\n\n' + '=' * 89 + '\nTool Started on: ' +
                str(starttime.strftime('%d-%b-%Y %I:%M %p')) + '\n')
except:
    error('Problem opening or writing to the polymetrics_log.txt file')

#----------------------------------------------------------------------------------
# Fire Metrics
#==================================================================================
def FireMetrics(args):
    try:
        # Only proceed if the required ArcGIS licenses are available
        if CheckArcInfo() == "yes" and CheckSpatialExt() == "yes":

            #======================================================================
            # Warn users that projections should match
            #----------------------------------------------------------------------
            display(
                '\n' + "*" * 60 + '\n'
                'Please verify spatial reference systems (SRS). \n'
                'Outputs will default to the SRS of the Wildfires layer. \n'
                'If the spatial references do not match, please reproject \n'
                'the input layers and rerun the tool. \n\n'
                '\n' + "*" * 60 + '\n', log
            )

            #======================================================================
            # Read user-defined parameters
            # ---------------------------------------------------------------------
            display('\n ... Reading user inputs', log)

            # inputs
            aoi = arcpy.GetParameterAsText(0)
            aoi_fld = arcpy.GetParameterAsText(1)
            wildfire_year = arcpy.GetParameterAsText(2)
            wfPrefix = arcpy.GetParameterAsText(3)
            outWksp = arcpy.GetParameterAsText(4)
            snapRst = arcpy.GetParameterAsText(5)
            outCellSize = int(arcpy.GetParameterAsText(6))

            #======================================================================
            # Test naming conventions
            #----------------------------------------------------------------------
            try:
                isNameOk(wfPrefix)
                isPathOk(outWksp)
            except:
                sys.exit(0)  #terminate tool

            #======================================================================
            # Processing Environment
            #----------------------------------------------------------------------
            arcpy.env.workspace = outWksp
            arcpy.env.extent = aoi
            if snapRst != '':
                arcpy.env.snapRaster = snapRst
            arcpy.env.mask = aoi
            arcpy.env.cellSize = outCellSize

            #==================================================================
            # ANALYSIS
            #==================================================================
            display(' ... Intersecting aoi polygons with wildfires', log)

            #======================================================================
            # Get wildfire datasets and years
            #----------------------------------------------------------------------
            value_table = arcpy.ValueTable(2)
            value_table.loadFromString(wildfire_year)

            for i in range(0, value_table.rowCount):
                row = value_table.getRow(i)

                wildfires = value_table.getValue(i, 0)
                wfYear = value_table.getTrueValue(i, 1)

                # -----------------------------------------------------------------
                # Step 1: Pairwise Intersect aoi with wildfire polgyons
                # -----------------------------------------------------------------
                display(' ... Intersecting aoi polygons with wildfires', log)

                inFeatures = [aoi, wildfires]
                outFC = r'memory\FC_pi'
                arcpy.analysis.PairwiseIntersect(inFeatures, outFC, 'ALL')

                # -----------------------------------------------------------------
                # Step 2: Summarize polygons amd calculate sum of Areas (km2)
                # -----------------------------------------------------------------
                outTable = wfPrefix + '_' + str(wfYear) + '_sumArea'
                display(' ... Summarizing polygon areas (km2) to table: ' +
                        outTable, log)

                # Add and calcualte 'AREA_KM' in square kilometers
                try:
                    arcpy.management.AddField(
                        in_table = r'memory\FC_pi',
                        field_name = 'WF_AREA_KM',
                        field_type = 'DOUBLE',
                    )
                    arcpy.management.CalculateGeometryAttributes(
                        in_features = r'memory\FC_pi',
                        geometry_property = [['WF_AREA_KM', 'AREA']],
                        area_unit = 'SQUARE_KILOMETERS'
                    )

                except:
                    tbinfo = traceback.format_tb(sys.exc_info()[2])[0]
                    error('\nPYTHON ERRORS in CalculateGeometryAttributes():'
                          '\nTraceback Info:    ' + tbinfo +
                          '\nError Type:    ' + str(sys.exc_info()[0]) +
                          '\nError Info:    ' + str(sys.exc_info()[1]), log)

                arcpy.analysis.Statistics(
                    in_table = r'memory\FC_pi',
                    out_table = outTable,
                    statistics_fields = [['WF_AREA_KM', 'SUM']],
                    case_field = aoi_fld,
                    concatenation_separator = ''
                )

                # ---------------------------------------------------------------------
                # Step 3: Create raster from polygons
                # ---------------------------------------------------------------------
                display(' ... Converting polygons to raster ' +
                        wfPrefix + '_' + str(wfYear), log)
                outRst = fp(outWksp, wfPrefix + '_' + str(wfYear))

                arcpy.conversion.PolygonToRaster(
                    in_features = outFC,
                    value_field = 'YEAR',
                    out_rasterdataset = outRst,
                    cell_assignment = 'MAXIMUM_COMBINED_AREA'
                )

                # ---------------------------------------------------------------------
                # Step 6: Memory clean up
                # ---------------------------------------------------------------------
                display(' ... Cleaning up temporary data from memory', log)
                memList = [r'memory\rst1', r'memory\FC_pi']
                for mem in memList:
                    if arcpy.Exists(mem): arcpy.management.Delete(mem)

            log.close()

    except:
        tbinfo = traceback.format_tb(sys.exc_info()[2])[0]
        error('\nPYTHON ERRORS in main():'
              '\nTraceback Info:    ' + tbinfo +
              '\nError Type:    ' + str(sys.exc_info()[0]) +
              '\nError Info:    ' + str(sys.exc_info()[1]), log)
        log.close()

        # release data in memory
        memList = [r'memory\FC_pi', r'memory\rst1']
        for mem in memList:
            if arcpy.Exists(mem): arcpy.management.Delete(mem)


if __name__ == '__main__':
    FireMetrics(sys.argv)
