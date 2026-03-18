#----------------------------------------------------------------------------------
#                       Wildfire Metrics: Severity
#----------------------------------------------------------------------------------
# SCRIPT NAME:  wildfire_severity.py
#               v.2026.0318
#
# PURPOSE:      Calculate wildfire severity within defined caribou zones.
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
# OUTPUTS:      combines annual wildfire severity with annual wildfire rasters
#
# AUTHOR:       Julie Duval, fRI Research
#
# CREATED ON:   February 20th, 2026
#
# EDITORS:      Julie Duval, fRI Research
#
# LAST UPDATES: March 9, 2026
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
    logFile = fp(fpath, 'wildfire_severity_log.txt')
    log = open(logFile, 'a')
    log.write('\n\n' + '=' * 89 + '\nTool Started on: ' +
                str(starttime.strftime('%d-%b-%Y %I:%M %p')) + '\n')
except:
    error('Problem opening or writing to the wildfire_severity_log.txt file')

#----------------------------------------------------------------------------------
# Fire Metrics
#==================================================================================
def SeverityRasters(args):
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
            display(' ... Reading user inputs', log)

            # inputs
            src_fire = arcpy.GetParameterAsText(0)
            src_fire_naming = arcpy.GetParameterAsText(1)
            src_int = arcpy.GetParameterAsText(2)
            src_int_naming = arcpy.GetParameterAsText(3)
            src_salv = arcpy.GetParameterAsText(4)
            src_salv_naming = arcpy.GetParameterAsText(5)
            start_year = arcpy.GetParameterAsText(6)
            end_year = arcpy.GetParameterAsText(7)
            tblExport = arcpy.GetParameterAsText(8)

            for rstYear in range(start_year, end_year + 1):
                display(' ===== Processing wildfire year ' +
                         str(rstYear) + ' =====', log)

                rst_fire = fp(src_fire, src_fire_naming.replace('****', rstYear))

                # check if wildfire raster exists
                if arcpy.Exists(rst_fire):
                    rst_severity = fp(src_int,
                                       src_int_naming.replace('****', rstYear))
                    rst_salvage = fp(src_salv,
                                     src_salv_naming.replace('****', rstYear))

                    #==============================================================
                    # Processing Environment
                    #--------------------------------------------------------------
                    arcpy.env.extent = rst_fire

                    #==============================================================
                    # ANALYSIS
                    #==============================================================
                    # -------------------------------------------------------------
                    # Step 1: combine severity rasters to determine which cells
                    #         were identified as salvaged, while retaining the
                    #         severity
                    # -------------------------------------------------------------
                    display(' ... Isolating salvage harvest values', log)
                    # isolate salvage harvest values
                    salvage = arcpy.sa.Con(arcpy.Raster(rst_salvage), 1, 0,
                                            'Value = 11')

                    display(' ... Combining severity rasters', log)
                    # combine severity rasters
                    rst_intxsalv = arcpy.sa.Combine([rst_severity, salvage])

                    # create raster layer
                    arcpy.management.MakeRasterLayer(
                        in_raster = rst_intxsalv,
                        out_rasterlayer = 'rst_intxsalv_lyr'
                    )

                    # identify field names
                    resultFields = arcpy.ListFields('rst_intxsalv_lyr')
                    intRstName = resultFields[3].name
                    salvRstName = resultFields[4].name

                    display(' ... Adding fields to output table', log)
                    # add output fields
                    fld_desc = [['SEVERITY', 'SHORT'],
                                ['SALVAGE', 'SHORT']]

                    arcpy.management.AddFields(
                        in_table = 'rst_intxsalv_lyr',
                        field_description = fld_desc
                    )

                    exprList = ['!{}!'.format(intRstName),
                                '!{}!'.format(salvRstName)]

                    display(' ... Calclating new fields', log)
                    # calculate fields
                    for i in range(0, len(fld_desc)):
                        arcpy.management.CalculateField(
                            in_table = 'rst_intxsalv_lyr',
                            field = fld_desc[i][0],
                            expression = exprList[i]
                        )

                    # drop fields
                    arcpy.management.DeleteField(
                        in_table = rst_intxsalv,
                        drop_field = [intRstName, salvRstName],
                        method = 'DELETE_FIELDS'
                    )

                    # -------------------------------------------------------------
                    # Step 2: combine fire bondary with severity values
                    # -------------------------------------------------------------
                    display(' ... Combining fire and severity rasters', log)

                    # combine fire and severity rasters
                    rst_combined = arcpy.sa.Combine([rst_fire, rst_intxsalv])

                    display(' ... Adding new fields to output table', log)

                    # add output fields
                    fld_desc = [['HERD_YEAR_FIREID', 'TEXT', '', 50],
                                ['SEVERITY', 'SHORT'],
                                ['SALVAGE', 'SHORT']]

                    arcpy.management.AddFields(
                        in_table = rst_combined,
                        field_description = fld_desc
                    )

                    display(' ... Populatinhg new fields', log)
                    # create raster layer
                    arcpy.management.MakeRasterLayer(
                        in_raster = rst_combined,
                        out_rasterlayer = 'rst_combo_lyr'
                    )

                    # identify field names
                    resultFields = arcpy.ListFields('rst_combo_lyr')
                    rst1Name = resultFields[3].name
                    rst2Name = resultFields[4].name

                    display(' ... Joining fire table and calculating values', log)
                    # join tables - with wildfire raster
                    join_table = arcpy.management.AddJoin(
                        in_layer_or_view = 'rst_combo_lyr',
                        in_field = rst1Name,
                        join_table = rst_fire,
                        join_field = 'Value'
                    )

                    # grab field name for combo table
                    flds = arcpy.ListFields(join_table)
                    combo_prefix = flds[0].name.split('.')[0]
                    jointbl_prefix = flds[len(flds)-1].name.split('.')[0]

                    # define expressions for calculation
                    expr = '!{}!'.format(jointbl_prefix + '.HERD_YEAR_FIREID')

                    # calculate fields in combo table
                    fld = combo_prefix + '.' + fld_desc[i][0]
                    arcpy.management.CalculateField(
                        in_table = join_table,
                        field = 'HERD_YEAR_FIREID',
                        expression = expr
                    )

                    # remove join
                    arcpy.management.RemoveJoin('rst_combo_lyr')

                    display(' ... Joining severity table and '
                            'calculating values', log)
                    # join tables - with wildfire severity raster
                    join_table = arcpy.management.AddJoin(
                        in_layer_or_view = 'rst_combo_lyr',
                        in_field = rst2Name,
                        join_table = rst_intxsalv,
                        join_field = 'Value'
                    )

                    # grab field name for combo table
                    flds = arcpy.ListFields(join_table)
                    combo_prefix = flds[0].name.split('.')[0]
                    jointbl_prefix = flds[len(flds)-1].name.split('.')[0]

                    fldList = ['SEVERITY', 'SALVAGE']
                    exprList = ['!{}!'.format(jointbl_prefix + '.SEVERITY'),
                                '!{}!'.format(jointbl_prefix + '.SALVAGE')]

                    # calculate fields in combo table
                    for i in range(0, len(exprList)):
                        fld = combo_prefix + '.' + fldList[i]
                        arcpy.management.CalculateField(
                            in_table = join_table,
                            field = fld,
                            expression = exprList[i]
                        )

                    # remove join
                    arcpy.management.RemoveJoin('rst_combo_lyr')

                    # drop fields
                    arcpy.management.DeleteField(
                        in_table = rst_combined,
                        drop_field = [rst1Name, rst2Name],
                        method = 'DELETE_FIELDS'
                    )

                    # -------------------------------------------------------------
                    # Step 3: Export table to csv file
                    # -------------------------------------------------------------
                    display(' ... Exporting table to csv', log)

                    arcpy.conversion.ExportTable(
                        in_table = rst_combined,
                        out_table = tblExport
                    )

                    # delete temporary rasters
                    for rst in [rst_combined, rst_intxsalv]:
                        if arcpy.Exists(rst): arcpy.management.Delete(rst)
                    arcpy.management.ClearWorkspaceCache()

            # close log file
            log.close()

    except:
        tbinfo = traceback.format_tb(sys.exc_info()[2])[0]
        error('\nPYTHON ERRORS in CombineRasters():'
              '\nTraceback Info:    ' + tbinfo +
              '\nError Type:    ' + str(sys.exc_info()[0]) +
              '\nError Info:    ' + str(sys.exc_info()[1]))
        log.close()

        # release data in memory
        for rst in [rst_combined, rst_intxsalv]:
            if arcpy.Exists(rst): arcpy.management.Delete(rst)
        arcpy.management.ClearWorkspaceCache()

if __name__ == '__main__':
    SeverityRasters(sys.argv)
