#----------------------------------------------------------------------------------
#                       Combine Output csv Files
#----------------------------------------------------------------------------------
# SCRIPT NAME:  combine_output_files.py
#               v.2026.0325
#
# PURPOSE:      Combines annual output files into one merged csv
#
# OUTPUTS:      merged csv file
#
# AUTHOR:       Julie Duval, fRI Research
#
# CREATED ON:   March 3, 2026
#
# LAST UPDATES: March 25, 2026
#
# NOTES:        tested with ArcGIS PRO 3.6.2
#               requires Advanced licensing with Spatial Analyst extension
#
#==================================================================================
# Import libraries
import os, sys
import csv
from os.path import join as fp
import arcpy
from functions import display, error, warning

def main():
    #======================================================================
    # Read user-defined parameters
    # ---------------------------------------------------------------------
    display(' ... Reading user inputs')

    # inputs
    combined_output_path = arcpy.GetParameterAsText(0)
    file_name_template = arcpy.GetParameterAsText(1)
    combined_output = arcpy.GetParameterAsText(2)

    # Grab list of all fires following template name
    arcpy.env.workspace = combined_output_path

    fileSearch = file_name_template + "*.csv"
    fileList = arcpy.ListFiles(fileSearch)
    display(' ... {} files found'.format(len(fileList)))

    with open(combined_output, 'w') as outfile:

        # save the header from the first input file
        save_first_header = True

        for filename in fileList:

            with open(fp(combined_output_path, filename), 'r') as f:

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
