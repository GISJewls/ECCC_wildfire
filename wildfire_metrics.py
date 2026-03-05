#----------------------------------------------------------------------------------
#               Wildfire Metrics: Fire frequency per pixel
#----------------------------------------------------------------------------------
# SCRIPT NAME:  wildfire_metrics.py
#               v.2026.0305
#
# PURPOSE:      Generate raster showing frequency of fire over time
#
# ARGUMENTS:    name        Type    Input Description
#              --------------------------------------------------------------------
#               inputRasters <R>    List of rasters to process
#               outputLocation <R>  Output workspace path
#               rasterName   <R>    Output raster name prefix
#               statList     <R>    List of statistics to run
#               aoi          <R>    Polygon layer to run statistics with
#               aoi_fld      <R>    Unique field from aoi polygon layer
#
# OUTPUTS:      rasters based on statistics
#               Tabulated summaries based on statistics using aoi as zones
#
# AUTHOR:       Julie Duval, fRI Research
#
# CREATED ON:   March 3, 2026
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
    logFile = fp(fpath, 'wildfire_metrics_tool_log.txt')
    log = open(logFile, 'a')
    log.write('\n\n' + '=' * 89 + '\nTool Started on: ' +
                str(starttime.strftime('%d-%b-%Y %I:%M %p')) + '\n')
except:
    error('Problem opening or writing to the frequency_tool_log.txt file')

#==================================================================================
# Fire Frequency
#==================================================================================
def FireStatistics(args):
    try:
        # Only proceed if the required ArcGIS licenses are available
        if CheckArcInfo() == "yes" and CheckSpatialExt() == "yes":

            #======================================================================
            # Read user-defined parameters
            #----------------------------------------------------------------------
            display('\n ... Reading user inputs', log)

            # inputs
            inputRasters = (arcpy.GetParameterAsText(0)).split(";")
            outputLocation = arcpy.GetParameterAsText(1)
            rasterName = arcpy.GetParameterAsText(2)
            statList = (arcpy.GetParameterAsText(3)).split(";")
            aoi = arcpy.GetParameterAsText(4)
            aoi_fld = arcpy.GetParameterAsText(5)

            #======================================================================
            # Test naming conventions
            #----------------------------------------------------------------------
            try:
                isNameOk(rasterName)
                isPathOk(outputLocation)
            except:
                sys.exit(0)  #terminate tool

            #======================================================================
            # Build list of rasters to process
            #----------------------------------------------------------------------
            display(' ... Creating list of input rasters', log)
            rstList = []
            for r in inputRasters:
                rstList.append(arcpy.Raster(r))

            #======================================================================
            # Convert aoi to raster for more efficient processing
            #----------------------------------------------------------------------
            display(' ... Converting input polygons to a temporary raster', log)
            outRst = r'memory\aoi_rst'

            with arcpy.EnvManager(cellSize = inputRasters[0],
                                  snapRaster = inputRasters[0],
                                  outputCoordinateSystem = inputRasters[0]):
                arcpy.conversion.PolygonToRaster(
                    in_features = aoi,
                    value_field = aoi_fld,
                    out_rasterdataset = outRst,
                    cell_assignment = 'MAXIMUM_COMBINED_AREA'
                )

            #======================================================================
            # ANALYSIS
            #======================================================================

            #======================================================================
            # Processing Environment
            #----------------------------------------------------------------------
            arcpy.env.workspace = outputLocation
            arcpy.env.extent = aoi
            arcpy.env.snapRaster = inputRasters[0]
            arcpy.env.mask = aoi
            arcpy.env.cellSize = inputRasters[0]
            arcpy.env.outputCoordinateSystem = inputRasters[0]

            # ---------------------------------------------------------------------
            # Step 1: Raster Calculator
            # ---------------------------------------------------------------------
            display(' ... Running cell statistics', log)

            for stat in statList:
                display('     ***** ' + stat + ' *****', log)
                rstOutput = fp(outputLocation, rasterName + '_' + stat)

                statConList = []
                for r in inputRasters:
                    if stat == 'COUNT':
                        statCon = arcpy.sa.Con(arcpy.sa.IsNull(r), 1, 0, 'VALUE=0')
                    else:
                        statCon = r

                    statConList.append(statCon)

                if stat == 'COUNT':
                    rst =  arcpy.sa.CellStatistics(statConList, 'SUM', 'DATA')
                else:
                    rst =  arcpy.sa.CellStatistics(statConList, stat, 'DATA')

                # -----------------------------------------------------------------
                # Step 2: Save raster
                # -----------------------------------------------------------------
                display('     ... Saving output raster ', log)
                rst.save(rstOutput)

                # -----------------------------------------------------------------
                # Step 3: Tabulate area to table
                # -----------------------------------------------------------------
                display('     ... Tabulating results', log)
                outTable = fp(outputLocation, rasterName + '_summary_' + stat)

                arcpy.sa.TabulateArea(
                    in_zone_data = r'memory\aoi_rst',
                    zone_field = aoi_fld,
                    in_class_data = rstOutput,
                    class_field = 'VALUE',
                    out_table = outTable,
                    processing_cell_size = rstOutput,
                    classes_as_rows = 'CLASSES_AS_ROWS'
                )

            log.close()

    except:
        tbinfo = traceback.format_tb(sys.exc_info()[2])[0]
        error('\nPYTHON ERRORS in main():'
              '\nTraceback Info:    ' + tbinfo +
              '\nError Type:    ' + str(sys.exc_info()[0]) +
              '\nError Info:    ' + str(sys.exc_info()[1]),
              log)
        log.close()

if __name__ == '__main__':
    FireStatistics(sys.argv)
