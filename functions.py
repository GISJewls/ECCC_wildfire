#----------------------------------------------------------------------------------
#                             Shared Functions
#----------------------------------------------------------------------------------
# SCRIPT NAME:  functions.py
#               v.2026.0304
#
# PURPOSE:      Share common functions between scripts.
#
# NOTES:        IMPORTANT NOTE FOR DEBUGGING - this script is imported to other
#               script tools.  If any edits to this script are done while an
#               ArcGISPro session is active, the changes made to this script will
#               not automatically apply.  You must save and close your ArcGISPro
#               session and start a new one in order to flush out the session's
#               memory.
#
# EDITORS:      Julie Duval, GIS Services Manager, fRI Research
#
# CREATED:      October 2018
#
# LAST UPDATES: Mar 2026 (J.Duval)  - Adapted for new tool
#
# ---------------------------------------------------------------------------------
# SCRIPT FUNCTIONS:
#       main(args)                 - Main function
#       isNameOk(folderName)       - Test folder name to make sure it meets ArcGIS
#                                    naming requirements
#       isPathOk(toolPath)         - Check path characters to see if potential
#                                    errors may exist
#       display(msg, log)          - Displays detailed messages (optional)
#       error(msg)                 - Displays error messages to user
#==================================================================================
import arcpy
import sys, string, os
import shutil
import traceback

class nameError(Exception):
    pass

class numError(Exception):
    pass

#**********************************************************************************
#***************************** FOLDER NAME CHECK **********************************
#**********************************************************************************
def isNameOk(folderName):
    '''Test folder name to make sure it meets ArcGIS naming requirements'''
    try:
        punctuations = ['.', '?', '-', '//', '...', ',', '!', '<', '>', ''',
                        '(', ')','[', ']', ':', ';', '{', '}', ''', '%', '#',
                        '^', '&', '*', '@', '$', ' ']

        # check for spaces, punctuations and special characters
        for p in punctuations:
            if p in folderName: raise nameError

        # check if folder starts with a number
        if folderName[0].isdigit():
            raise numError

        # If no errors raised, return True
        return True

    except nameError:
        error('!!! Output folder name "' + folderName + '" should not contain '
              'any spaces or punctuations.')
        error('!!! Only underscores are allowed.')
        sys.exit(0)  #terminate tool

    except numError:
        error('!!! Output folder name "' + folderName + '" should not start '
              'with a number.')
        sys.exit(0)  #terminate tool

    except:
        print((arcpy.GetMessages(2))); raise

#**********************************************************************************
#********************************** PATH NAME CHECK *******************************
#**********************************************************************************
def isPathOk(pathName):
    '''Test path to make sure it meets ArcGIS naming requirements'''
    try:
        punctuations = ['?', '-', '//', '...', ',', '!', '<', '>', ''',
                        '(', ')','[', ']', ';', '{', '}', ''', '%', '#', '^',
                        '&', '*', '@', '$', ' ']
        # Split the pathName into a list of each sub-folder
        pathSplit = pathName.split('\\')

        # check for spaces, punctuations and special characters
        for subfld in pathSplit:
            for p in punctuations:
                if p in subfld:
                    raise nameError

            # check if sub-folder starts with a number
            #if subfld[0].isdigit(): raise numError

        # If no errors raised, return True
        return True

    except nameError:
        error('!!! Output path name should not contain any spaces or ' +
              'punctuations. Only underscores are allowed.')
        error('folder in question: ' + subfld)
        sys.exit(0) #terminate tool

    except numError:
        error('\n!!! Output path name should not have a folder that starts '
                'with a number: \n' + subfld)
        sys.exit(0)  #terminate tool

    except:
        print((arcpy.GetMessages(2))); raise


#**********************************************************************************
#************************* OUTPUT MESSAGES FORMATTING *****************************
#**********************************************************************************
def display(msg, log = False):
    '''Displays detailed processing messages to user'''
    arcpy.AddMessage(msg)
    if log != False:
        log.write(msg + '\n')

def error(msg, log = False):
    '''Displays error messages to user'''
    arcpy.AddError(msg)
    if log != False:
        log.write(msg + '\n')

def warning(msg, log = False):
    '''Displays error messages to user'''
    arcpy.AddWarning(msg)
    if log != False:
        log.write(msg + '\n')


#**********************************************************************************
#************************************ MAIN ****************************************
#**********************************************************************************
def main():
    print('This module contains common funtions shared between tools.')

if __name__ == '__main__':
    main()
