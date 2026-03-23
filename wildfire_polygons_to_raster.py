#----------------------------------------------------------------------------------
#            Wildfire Metrics: Area Burned and Annual Wildfire Rasters
#----------------------------------------------------------------------------------
# SCRIPT NAME:  wildfire_polygons_to_raster.py
#               v.2026.0323
#
# PURPOSE:      Calculate wildfire metrics (area) within defined caribou zones.
#
# ARGUMENTS:    name        Type    Input Description
#              --------------------------------------------------------------------
#               aoi         <R>     Area of interest (herd boundaries)
#               aoi_fld     <R>     Unique field from aoi
#               wildfireList <R>    Annual wildfire data, polygons (multiple)
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
# LAST UPDATES: March 3, 2026
#               March 13, 2026  - debugging and improving code
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
    logFile = fp(fpath, 'polygons_to_raster_log.txt')
    log = open(logFile, 'a')
    log.write('\n\n' + '=' * 89 + '\nTool Started on: ' +
                str(starttime.strftime('%d-%b-%Y %I:%M %p')) + '\n')
except:
    error('Problem opening or writing to the polygons_to_raster_log.txt file')

#----------------------------------------------------------------------------------
# Fire Metrics
#==================================================================================
def WildfirePolygonsToRaster(args):
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
            csvWksp = arcpy.GetParameterAsText(8)

            display('\nArea of interest:        ' + aoi +
                    '\nField to define AOI:     ' + aoi_fld +
                    '\n# of wildfire layers:    ' + str(len(wildfireList)) +
                    '\nWildfire year field:     ' + wf_year_fld +
                    '\nWildfire ID field:       ' + wf_id_fld +
                    '\nOuptut prefix            ' + wfPrefix +
                    '\nOutput workspace         ' + outWksp +
                    '\nSnap raster              ' + snapRst +
                    '\nOutput folder - tables:  ' + csvWksp +
                    '\n\n', log)

            # set main script variables
            tempFC = fp(outWksp, 'FC_pi')

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
            #arcpy.env.mask = aoi
            arcpy.env.snapRaster = snapRst
            arcpy.env.cellSize = snapRst

            #======================================================================
            # ANALYSIS
            #======================================================================
            # create list to keep track of years with no wildfires
            noWildfires = []

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

                display('\n ... Processing for wildfire year ' + str(wfYear), log)

                # define output variables
                statTable = 'memory\\' + wfPrefix + '_' + str(wfYear) + '_sumArea'
                outRst = fp(outWksp, wfPrefix + '_' + str(wfYear))
                rstTable = fp(outWksp, wfPrefix + '_' + str(wfYear) + '_tbl')

                # -----------------------------------------------------------------
                # Step 1: Pairwise Intersect aoi with wildfire polgyons
                # -----------------------------------------------------------------
                display('     - Intersecting aoi polygons with wildfires', log)

                inFeatures = [aoi, wildfires]
                arcpy.analysis.PairwiseIntersect(inFeatures, tempFC, 'ALL')

                # check if any results exist
                arcpy.management.MakeFeatureLayer(
                    in_features = tempFC,
                    out_layer = 'FC_lyr'
                )
                result = arcpy.management.GetCount('FC_lyr')
                count = int(result[0])

                if count != 0:
                    # -------------------------------------------------------------
                    # Step 2: Add and calculate new fields
                    # -------------------------------------------------------------
                    display('     - Adding new fields to polygon layer', log)

                    # repair any geometry issues
                    arcpy.management.RepairGeometry(
                        in_features = tempFC,
                        delete_null = "DELETE_NULL",
                        validation_method = "ESRI"
                    )

                    # Add and calculate 'AREA_KM2' in square kilometers
                    arcpy.management.AddField(
                        in_table = tempFC,
                        field_name = 'POLY_AREA_KM2',
                        field_type = 'DOUBLE',
                    )
                    arcpy.management.CalculateGeometryAttributes(
                        in_features = tempFC,
                        geometry_property = [['POLY_AREA_KM2', 'AREA']],
                        area_unit = 'SQUARE_KILOMETERS'
                    )

                    # Add and calculale 'HERD_YEAR_FIREID'
                    fld = 'HERD_YEAR_FIREID'
                    if fType == 'TEXT':
                        fStr = '!{}! + "_" + str(int(!{}!)) + "_" + str(!{}!)'
                    else:
                        fStr = '!{}! + "_" + str(int(!{}!)) + "_" + str(int(!{}!))'

                    expr = fStr.format(aoi_fld, wf_year_fld, wf_id_fld)

                    arcpy.management.AddField(
                        in_table = tempFC,
                        field_name = fld,
                        field_type = 'TEXT',
                        field_length = 50
                    )

                    fld_desc = [[fld, 'TEXT', '', 50]]

                    arcpy.management.AddFields(
                        in_table = tempFC,
                        field_description = fld_desc
                    )

                    arcpy.management.CalculateField(
                        in_table = tempFC,
                        field = fld,
                        expression = str(expr)
                    )

                    # -------------------------------------------------------------
                    # Step 3: Summarize polygon areas by herd, year, and fireID
                    # -------------------------------------------------------------
                    display('     - Summarizing polygon areas', log)
                    arcpy.analysis.Statistics(
                        in_table = tempFC,
                        out_table = statTable,
                        statistics_fields = [['POLY_AREA_KM2', 'SUM']],
                        case_field = ['HERD_YEAR_FIREID'],
                    )

                    # -------------------------------------------------------------
                    # Step 4: Convert polygons to raster
                    # -------------------------------------------------------------
                    display('     - Converting polygons to raster: ' +
                            wfPrefix + '_' + str(wfYear), log)

                    memRst = r'memory\xtempRst'
                    arcpy.conversion.FeatureToRaster(
                        in_features  = tempFC,
                        field = fld,
                        out_raster = memRst,
                        cell_size = arcpy.env.cellSize
                    )

                    arcpy.Raster(memRst).save(outRst)
                    arcpy.management.Delete(memRst)

                    # -------------------------------------------------------------
                    # Step 5: Add new fields to raster attribute table
                    # -------------------------------------------------------------
                    display('     - Adding new fields to raster attribute table',
                            log)

                    # Create a copy of the raster table as a workaround.
                    # Working directly from the raster table created unknown and
                    # (at the time) unsolvable errors
                    arcpy.conversion.ExportTable(
                        in_table = outRst,
                        out_table = rstTable
                    )

                    if fType == 'TEXT':
                        addFL = 'TEXT, "", ' + str(fLength)
                    else:
                        addFL = fType

                    fld_desc = [['HERD', 'TEXT', '', 20],
                                ['PROV', 'TEXT', '', 20],
                                ['YEAR', 'SHORT'],
                                ['FIREID', addFL],
                                ['POLY_AREA_KM2', 'DOUBLE'],
                                ['RAST_AREA_KM2', 'DOUBLE']]

                    arcpy.management.AddFields(
                        in_table = rstTable,
                        field_description = fld_desc
                    )

                    # -------------------------------------------------------------
                    # Step 6: Calculate attributes
                    # -------------------------------------------------------------
                    display('     - Calculating attributes', log)

                    # create raster table view for join operation
                    arcpy.management.MakeTableView(
                        in_table = rstTable,
                        out_view = 'rstTbl_View'
                    )

                    # join raster table and polygon tables
                    join_table = arcpy.management.AddJoin(
                        in_layer_or_view = 'rstTbl_View',
                        in_field = fld,
                        join_table = statTable,
                        join_field = fld
                    )

                    # grab field name prefixes from joined tables
                    flds = arcpy.ListFields(join_table)
                    rtbl_prefix = flds[0].name.split('.')[0]
                    jtbl_prefix = flds[len(flds)-1].name.split('.')[0]

                    # field names to calculate
                    fldNames = ['HERD', 'PROV', 'YEAR', 'FIREID',
                                'POLY_AREA_KM2', 'RAST_AREA_KM2']

                    # define expressions for calculation
                    exprList = [
                        '!{}!.split("_")[0]'.format(jtbl_prefix + '.' + fld),
                        '!{}!.split("_")[1]'.format(jtbl_prefix + '.' + fld),
                        'int(!{}!.split("_")[2])'.format(jtbl_prefix + '.' + fld),
                        'str(!{}!.split("_")[3])'.format(jtbl_prefix + '.' + fld),
                        '!{}!'.format(jtbl_prefix + '.SUM_POLY_AREA_KM2'),
                        '!{}! * 0.0009'.format(str(rtbl_prefix + '.Count'))
                    ]

                    # loop to calculate fields
                    for i in range(0, len(fldNames)):
                        arcpy.management.CalculateField(
                            in_table = 'rstTbl_View',
                            field = fldNames[i],
                            expression = exprList[i]
                        )

                    # remove join
                    arcpy.management.RemoveJoin('rstTbl_View')

                    # -------------------------------------------------------------
                    # Step 7: Export final table to csv
                    # -------------------------------------------------------------
                    display('     - Exporting raster attributes to csv', log)

                    tblExport = fp(csvWksp, wfPrefix + '_' + str(wfYear) + '.csv')
                    arcpy.conversion.ExportTable(
                        in_table = rstTable,
                        out_table = tblExport
                    )

                    # clear workspace cache
                    arcpy.management.ClearWorkspaceCache()

                # no records available
                else:
                    display('     !!! No wildfires found for ' + str(wfYear), log)
                    noWildfires.append(wfYear)

                # -----------------------------------------------------------------
                # Step 8: Memory clean up
                # -----------------------------------------------------------------
                memList = [tempFC, rstTable, statTable]
                for mem in memList:
                    if arcpy.Exists(mem):
                        arcpy.management.Delete(mem)

            # display list of years with no wildfires (if any)
            numYears = len(noWildfires)
            if numYears > 0:
                display('\nThe following {} years had no wildfires occur within '
                        'the area of interest'.format(str(numYears)), log)
                for yr in noWildfires:
                    display(str(yr), log)

            # close log file
            log.close()

    except:
        tbinfo = traceback.format_tb(sys.exc_info()[2])[0]
        error('\nPYTHON ERRORS in WildfirePolygonsToRaster():'
              '\nTraceback Info:    ' + tbinfo +
              '\nError Type:    ' + str(sys.exc_info()[0]) +
              '\nError Info:    ' + str(sys.exc_info()[1]), log)
        log.close()

        # release data in memory
        memList = [tempFC, rstTable, statTable]
        for mem in memList:
            if arcpy.Exists(mem): arcpy.management.Delete(mem)
        arcpy.management.ClearWorkspaceCache()

if __name__ == '__main__':
    WildfirePolygonsToRaster(sys.argv)
