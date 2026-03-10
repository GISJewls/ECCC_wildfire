#----------------------------------------------------------------------------------
#                   Wildfire Metrics: Create Range Rasters
#----------------------------------------------------------------------------------
# SCRIPT NAME:  range_polygons_to_raster.py
#               v.2026.0309
#
# PURPOSE:      Create herd range rasters from polygons
#
# ARGUMENTS:    name        Type    Input Description
#              --------------------------------------------------------------------
#               aoi         <R>     Area of interest (herd boundaries)
#               aoi_fld     <R>     Unique field from aoi
#               wildfireList <R>     Annual wildfire data, polygons (multiple)
#               wf_year_fld <R>     Wildfire year, field
#               wf_id_fld   <R>     Wildfire identifier, field
#               wfPrefix    <R>     Prefix used for outputs, string
#               outWksp     <R>     Output workspace
#               snapRst     <O>     Snap raster
#               outCellSize <R>     Output raster cell size, default = 30m
#
# OUTPUTS:      summary tables and integer attributed raster
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
                'the input layers and rerun the tool. '
                '\n' + "*" * 60 + '\n', log
            )

            #======================================================================
            # Read user-defined parameters
            # ---------------------------------------------------------------------
            display('\n ... Reading user inputs', log)

            # inputs
            aoi = arcpy.GetParameterAsText(0)
            aoi_fld = arcpy.GetParameterAsText(1)
            wildfireList = arcpy.GetParameterAsText(2).split(';')
            wf_year_fld = arcpy.GetParameterAsText(3)
            wf_id_fld = arcpy.GetParameterAsText(4)
            wfPrefix = arcpy.GetParameterAsText(5)
            outWksp = arcpy.GetParameterAsText(6)
            snapRst = arcpy.GetParameterAsText(7)
            outCellSize = int(arcpy.GetParameterAsText(8))

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

            #======================================================================
            # ANALYSIS
            #======================================================================

            #======================================================================
            # Loop through wildfire datasets
            #----------------------------------------------------------------------
            for i in range(0, len(wildfireList)):

                wildfires = wildfireList[i]

                # get year of wildfire
                with arcpy.da.SearchCursor(wildfires, [wf_year_fld]) as cursor:
                    for row in cursor:
                        wfYear = int(float(row[0]))
                        break

                # get wildfire id field type
                fields = arcpy.ListFields(wildfires)
                for field in fields:
                    if field.name == wf_id_fld:
                        fType = field.type
                        if fType == 'TEXT':
                            fLength = field.length



                display(' ... Processing for wildfire year ' + str(wfYear), log)

##                # -----------------------------------------------------------------
##                # Step 1: Pairwise Intersect aoi with wildfire polgyons
##                # -----------------------------------------------------------------
##                display('     - Intersecting aoi polygons with wildfires', log)
##
##                inFeatures = [aoi, wildfires]
##                memFC = r'memory\FC_pi'
##                arcpy.analysis.PairwiseIntersect(inFeatures, memFC, 'ALL')
##
##                # -----------------------------------------------------------------
##                # Step 2: Summarize polygons amd calculate sum of Areas (km2)
##                # -----------------------------------------------------------------
##                outTable = wfPrefix + '_' + str(wfYear) + '_sumArea'
##                display('     - Summarizing polygon areas (km2) to table: ' +
##                        outTable, log)

                # Add and calcualte 'AREA_KM2' in square kilometers
                try:
                    arcpy.management.AddField(
                        in_table = memFC,
                        field_name = 'WF_AREA_KM2',
                        field_type = 'DOUBLE',
                    )
                    arcpy.management.CalculateGeometryAttributes(
                        in_features = memFC,
                        geometry_property = [['WF_AREA_KM2', 'AREA']],
                        area_unit = 'SQUARE_KILOMETERS'
                    )

                except:
                    tbinfo = traceback.format_tb(sys.exc_info()[2])[0]
                    error('\nPYTHON ERRORS in CalculateGeometryAttributes():'
                          '\nTraceback Info:    ' + str(tbinfo) +
                          '\nError Type:    ' + str(sys.exc_info()[0]) +
                          '\nError Info:    ' + str(sys.exc_info()[1]))

                arcpy.analysis.Statistics(
                    in_table = r'memory\FC_pi',
                    out_table = outTable,
                    statistics_fields = [['WF_AREA_KM2', 'SUM']],
                    case_field = aoi_fld,
                    concatenation_separator = ''
                )

                # -----------------------------------------------------------------
                # Step 3: Create raster from polygons
                # -----------------------------------------------------------------
                display('     - Converting polygons to raster: ' +
                        wfPrefix + '_' + str(wfYear), log)
                outRst = fp(outWksp, wfPrefix + '_' + str(wfYear))

                fld = 'siteID_PRNAME'

                arcpy.conversion.PolygonToRaster(
                    in_features = memFC,
                    value_field = fld,
                    out_rasterdataset = outRst,
                    cell_assignment = 'MAXIMUM_COMBINED_AREA'
                )

                # -----------------------------------------------------------------
                # Step 4: Add year and fireID fields to new raster
                # -----------------------------------------------------------------
                display('     - Adding range, province, year, and fire ID to '
                        'raster attribute table')

                if fType == 'TEXT':
                    addFL = 'TEXT, "", ' + str(fLength)
                else:
                    addFL = fType

                fldNames = ['RANGE', 'PROV', 'YEAR', 'FIREID']
                exprList = ['!{}!.split("_")[0]'.format(fld),
                            '!{}!.split("_")[1]'.format(fld),
                            'int(!{}!.split("_")[2])'.format(fld),
                            'str(!{}!.split("_")[3])'.format(fld)]

                fld_desc = [['RANGE', 'TEXT', '', 20],
                            ['PROV', 'TEXT', '', 20],
                            ['YEAR', 'SHORT'],
                            ['FIREID', addFL]]
                try:
                    arcpy.management.AddFields(
                        in_table = outRst,
                        field_description = fld_desc)

                    for i in range(0, len(fldNames)):
##                        arcpy.management.AddField(
##                            in_table = outRst,
##                            field_name = fldNames[i],
##                            field_type = fldTypes[i] +
##                            fldLengths[i]
##                        )

                        arcpy.management.CalculateField(
                            in_table = outRst,
                            field = fldNames[i],
                            expression = exprList[i]
                        )

                except:
                    tbinfo = traceback.format_tb(sys.exc_info()[2])[0]
                    error('\nPYTHON ERRORS in Step 4:'
                          '\nTraceback Info:    ' + str(tbinfo) +
                          '\nError Type:    ' + str(sys.exc_info()[0]) +
                          '\nError Info:    ' + str(sys.exc_info()[1]), log)

                # -----------------------------------------------------------------
                # Step 5: Export to csv
                # -----------------------------------------------------------------
                display('     - Exporting raster attributes to csv')

                # Create the required FieldMap and FieldMappings objects
                fm_wf = arcpy.FieldMap()
                fms = arcpy.FieldMappings()

                # Add fields to the FieldMap object
                fm_wf.addInputField(outRst, 'HERD_YEAR_FIREID')
                fm_wf.addInputField(outRst, 'RANGE')
                fm_wf.addInputField(outRst, 'PROV')
                fm_wf.addInputField(outRst, 'YEAR')
                fm_wf.addInputField(outRst, 'FIREID')
                fm_wf.addInputField(outRst, 'COUNT')
                fm_wf.addInputField(outRst, 'AREA_KM2')

                # Add the FieldMap objects to the FieldMappings object
                fms.addFieldMap(fm_wf)

                csvWksp = r'W:\Caribou\Projects\2025_ECCCFire\GIS_Analysis\outputs'
                tblExport = fp(csvWksp, wfPrefix + '_' + str(wfYear) + '.csv')
                arcpy.conversion.ExportTable(
                    in_table = outRst,
                    out_table = tblExport,
                    field_mapping = fms
                )

                # -----------------------------------------------------------------
                # Step 6: Memory clean up
                # -----------------------------------------------------------------
                memList = [r'memory\FC_pi']
                for mem in memList:
                    if arcpy.Exists(mem): arcpy.management.Delete(mem)

            log.close()

    except:
        tbinfo = traceback.format_tb(sys.exc_info()[2])[0]
        error('\nPYTHON ERRORS in main():'
              '\nTraceback Info:    ' + tbinfo +
              '\nError Type:    ' + str(sys.exc_info()[0]) +
              '\nError Info:    ' + str(sys.exc_info()[1]))
        log.close()

        # release data in memory
        memList = [r'memory\rst1']
        for mem in memList:
            if arcpy.Exists(mem): arcpy.management.Delete(mem)


if __name__ == '__main__':
    FireMetrics(sys.argv)
