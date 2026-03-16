#-------------------------------------------------------------------------------
# Name:        combine_output_files.py
# Purpose:
#
# Author:      jduval
#
# Created:     13/03/2026
# Copyright:   (c) jduval 2026
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os, sys
import csv
from os.path import join as fp

def main():

    combined_output_path = r'W:\Caribou\Projects\2025_ECCCFire\GIS_Analysis\outputs'
    combined_output = fp(combined_output_path, 'NBAC_MB1_Merged.csv')

    fileList = []

    file_name_template = 'NBAC_MB1_****.csv'
    yearStart = 1972
    yearEnd = 2024

    # Grab list of all fires following template name
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
