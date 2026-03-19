#----------------------------------------------------------------------------------
#            Wildfire Metrics: Combine output csv files
#----------------------------------------------------------------------------------
# SCRIPT NAME:  combine_output_files.py
#               v.2026.0317
#
# PURPOSE:      Combines annual output files into one merged csv
#
# OUTPUTS:      merged csv file
#
# AUTHOR:       Julie Duval, fRI Research
#
# CREATED ON:   March 3, 2026
#
# EDITORS:      Julie Duval, fRI Research
#
# LAST UPDATES: March 17, 2026
#
# NOTES:        tested with ArcGIS PRO 3.6.2
#               requires Advanced licensing with Spatial Analyst extension
#
#==================================================================================
# Import libraries
import os, sys
import csv
from os.path import join as fp

def main():
    #======================================================================
    # Read user-defined parameters
    # ---------------------------------------------------------------------
    display(' ... Reading user inputs', log)

    # inputs
    combined_output_path = arcpy.GetParameterAsText(0)
    file_name_template = arcpy.GetParameterAsText(1)
    yearStart = int(arcpy.GetParameterAsText(2))
    yearEnd = int(arcpy.GetParameterAsText(3))
    combined_output = arcpy.GetParameterAsText(4)

    # Grab list of all fires following template name
    fileList = []
    for yr in range(yearStart, yearEnd + 1):
        inFile = fp(combined_output_path,
                    file_name_template.replace('****', str(yr)))
        if os.path.exists(inFile) == True:
            fileList.append(inFile)

    with open(combined_output, 'w') as outfile:

        # save the header from the first input file
        save_first_header = True

        for filename in fileList:

            with open(filename, 'r') as f:

                if save_first_header == False:
                    next(f)
                    for line in f:
                        outfile.write(line)
                        if not line.endswith('\n'):
                            outfile.write('\n')

                else:
                    save_first_header = False
                    for line in f:
                        outfile.write(line)
                        if not line.endswith('\n'):
                            outfile.write('\n')



    outfile.close()


if __name__ == '__main__':
    main()
