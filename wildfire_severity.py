#----------------------------------------------------------------------------------
#                             Wildfire Severity
#----------------------------------------------------------------------------------
# SCRIPT NAME:  wildfire_severity.py
#               v.2026.0323
#
# PURPOSE:      Extracts wildfire severity within defined caribou zones.  Overlaps
#               with annual widlfire rasters.
#
# ARGUMENTS:    name        Type    Input Description
#              --------------------------------------------------------------------
#               src_fire    <R>     Source fire raster
#               src_fire_naming <R> Fire raster naming template
#               src_sev     <R>     Source severity raster
#               src_sev_naming  <R> Severity raster naming template
#               src_salv    <R>     Post-harvest salvage raster
#               src_salv_naming <R> Salvage raster naming template
#               start_year  <R>     Start year
#               end_year    <R>     End year
#               outFolder   <R>     Output folder for csv files
#
# OUTPUTS:      combines annual wildfire severity with annual wildfire rasters
#
# AUTHOR:       Julie Duval, fRI Research
#
# CREATED ON:   February 20th, 2026
#
# LAST UPDATES: March 20, 2026
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
def WildfireSeverity(args):
    try:
        # Only proceed if the required ArcGIS licenses are available
        if CheckArcInfo() == "yes" and CheckSpatialExt() == "yes":

            #======================================================================
            # Read user-defined parameters
            # ---------------------------------------------------------------------
            display(' ... Reading user inputs', log)

            # inputs
            src_fire = arcpy.GetParameterAsText(0)
            src_fire_naming = arcpy.GetParameterAsText(1)
            src_sev = arcpy.GetParameterAsText(2)
            src_sev_naming = arcpy.GetParameterAsText(3)
            src_salv = arcpy.GetParameterAsText(4)
            src_salv_naming = arcpy.GetParameterAsText(5)
            start_year = int(arcpy.GetParameterAsText(6))
            end_year = int(arcpy.GetParameterAsText(7))
            outFolder = arcpy.GetParameterAsText(8)

            display('\nAnnual wildfires:        ' + src_fire +
                    '\nTemplate name:           ' + src_fire_naming +
                    '\nAnnual severity rasters: ' + src_sev +
                    '\nTemplate name:           ' + src_sev_naming +
                    '\nAnnual salvage rasters:  ' + src_salv +
                    '\nTemplate name:           ' + src_salv_naming +
                    '\nWildfire start year:     ' + start_year +
                    '\nWildfire end year:       ' + end_year +
                    '\nExport folder:           ' + outFolder +
                    '\n\n', log)


            for rstYear in range(start_year, end_year + 1):
                display('\n ===== Processing wildfire year ' +
                         str(rstYear) + ' =====', log)

                rst_fire = fp(src_fire,
                              src_fire_naming.replace('****', str(rstYear)))
                tblExport = fp(outFolder,
                    'fire_severity_' +
                    src_fire_naming.replace('****',  str(rstYear)) + '.csv'
                )

                # check if wildfire raster exists
                if arcpy.Exists(rst_fire):
                    rst_severity = fp(src_sev,
                                   src_sev_naming.replace('****', str(rstYear)))
                    rst_salvage = fp(src_salv,
                                   src_salv_naming.replace('****', str(rstYear)))

                    #==============================================================
                    # Processing Environment
                    #--------------------------------------------------------------
                    arcpy.env.extent = rst_fire
                    arcpy.env.workspace = arcpy.env.scratchGDB

                    #==============================================================
                    # ANALYSIS
                    #==============================================================
                    # -------------------------------------------------------------
                    # Step 1: combine severity rasters to determine which cells
                    #         were identified as salvaged, while retaining the
                    #         severity
                    # -------------------------------------------------------------
                    # isolate salvage harvest values
                    display(' ... Isolating salvage harvest values', log)
                    salvage = arcpy.sa.Con(arcpy.Raster(rst_salvage), 1, 0,
                                            'Value = 11')

                    # combine severity rasters
                    display(' ... Combining severity and salvage rasters', log)
                    severity = arcpy.Raster(rst_severity)
                    with arcpy.EnvManager(workspace = 'memory'):
                        rst_sevxsalv = arcpy.sa.Combine([severity, salvage])

                    # create raster layer
                    arcpy.management.MakeRasterLayer(
                        in_raster = rst_sevxsalv,
                        out_rasterlayer = 'rst_sevxsalv_lyr'
                    )

                    # identify field names
                    resultFields = arcpy.ListFields('rst_sevxsalv_lyr')
                    sevRstName = resultFields[3].name
                    salvRstName = resultFields[4].name

                    # add new fields
                    fld_desc = [['SEVERITY', 'SHORT'],
                                ['SALVAGE', 'SHORT']]

                    arcpy.management.AddFields(
                        in_table = 'rst_sevxsalv_lyr',
                        field_description = fld_desc
                    )

                    exprList = ['!{}!'.format(sevRstName),
                                '!{}!'.format(salvRstName)]

                    # calculate fields
                    for i in range(0, len(fld_desc)):
                        arcpy.management.CalculateField(
                            in_table = 'rst_sevxsalv_lyr',
                            field = fld_desc[i][0],
                            expression = exprList[i]
                        )

                    # drop fields
                    arcpy.management.DeleteField(
                        in_table = rst_sevxsalv,
                        drop_field = [sevRstName, salvRstName],
                        method = 'DELETE_FIELDS'
                    )

                    # -------------------------------------------------------------
                    # Step 2: combine fire boundary with severity values
                    # -------------------------------------------------------------
                    display(' ... Combining fire and severity rasters', log)

                    # combine fire and severity rasters
                    rst_combined = arcpy.sa.Combine([rst_fire, rst_sevxsalv])

                    # add new output fields
                    fld_desc = [['HERD_YEAR_FIREID', 'TEXT', '', 50],
                                ['HERD', 'TEXT', '', 20],
                                ['PROV', 'TEXT', '', 20],
                                ['YEAR', 'SHORT'],
                                ['FIREID', 'SHORT'],
                                ['SEVERITY', 'SHORT'],
                                ['SALVAGE', 'SHORT'],
                                ['RAST_AREA_KM2', 'DOUBLE']]

                    arcpy.management.AddFields(
                        in_table = rst_combined,
                        field_description = fld_desc
                    )

                    # create raster layer
                    arcpy.management.MakeRasterLayer(
                        in_raster = rst_combined,
                        out_rasterlayer = 'rst_combo_lyr'
                    )

                    # identify field names
                    resultFields = arcpy.ListFields('rst_combo_lyr')
                    rst1Name = resultFields[3].name
                    rst2Name = resultFields[4].name

                    # join tables - with wildfire raster
                    display(' ... Joining fire table and calculating values', log)

                    join_table = arcpy.management.AddJoin(
                        in_layer_or_view = 'rst_combo_lyr',
                        in_field = rst1Name,
                        join_table = rst_fire,
                        join_field = 'Value'
                    )

                    # grab field name for combo table
                    flds = arcpy.ListFields(join_table)
                    combo_prefix = flds[0].name.split('.')[0]
                    jtbl_prefix = flds[len(flds)-1].name.split('.')[0]

                    # field names to calculate
                    fldNames = ['HERD_YEAR_FIREID', 'HERD', 'PROV', 'YEAR',
                                'FIREID', 'RAST_AREA_KM2']

                    # define expressions for calculation
                    jtbl_fld = jtbl_prefix + '.HERD_YEAR_FIREID'
                    exprList = [
                        '!{}!'.format(jtbl_fld),
                        '!{}!.split("_")[0]'.format(jtbl_fld),
                        '!{}!.split("_")[1]'.format(jtbl_fld),
                        'int(!{}!.split("_")[2])'.format(jtbl_fld),
                        'int(!{}!.split("_")[3])'.format(jtbl_fld),
                        '!{}! * 0.0009'.format(str(combo_prefix + '.Count'))
                    ]

                    # loop to calculate fields
                    for i in range(0, len(fldNames)):
                        arcpy.management.CalculateField(
                            in_table = join_table,
                            field = combo_prefix + '.' + fldNames[i],
                            expression = exprList[i]
                        )

                    # remove join
                    arcpy.management.RemoveJoin('rst_combo_lyr')

                    # -------------------------------------------------------------
                    # join tables - with wildfire severity raster
                    display(' ... Joining severity table and '
                            'calculating values', log)

                    join_table = arcpy.management.AddJoin(
                        in_layer_or_view = 'rst_combo_lyr',
                        in_field = rst2Name,
                        join_table = rst_sevxsalv,
                        join_field = 'Value'
                    )

                    # grab field name for combo table
                    flds = arcpy.ListFields(join_table)
                    combo_prefix = flds[0].name.split('.')[0]
                    jtbl_prefix = flds[len(flds)-1].name.split('.')[0]

                    fldList = ['SEVERITY', 'SALVAGE']
                    exprList = ['!{}!'.format(jtbl_prefix + '.SEVERITY'),
                                '!{}!'.format(jtbl_prefix + '.SALVAGE')]

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
                    display(' ... Exporting combined table to csv', log)

                    arcpy.conversion.ExportTable(
                        in_table = rst_combined,
                        out_table = tblExport
                    )

                    # delete temporary rasters
                    for rst in [rst_combined, rst_sevxsalv, salvage,
                                'rst_sevxsalv_lyr', 'rst_combo_lyr']:
                        arcpy.management.Delete(rst)
                    arcpy.management.ClearWorkspaceCache()

                else:
                    display(' ... No wildfires occurred within aoi')
            # close log file
            log.close()

    except:
        tbinfo = traceback.format_tb(sys.exc_info()[2])[0]
        error('\nPYTHON ERRORS in CombineRasters():'
              '\nTraceback Info:    ' + tbinfo +
              '\nError Type:    ' + str(sys.exc_info()[0]) +
              '\nError Info:    ' + str(sys.exc_info()[1]), log)
        log.close()

        # release data in memory
        for rst in [rst_combined, rst_sevxsalv, salvage]:
            if arcpy.Exists(rst): arcpy.management.Delete(rst)
        arcpy.management.ClearWorkspaceCache()

if __name__ == '__main__':
    WildfireSeverity(sys.argv)
