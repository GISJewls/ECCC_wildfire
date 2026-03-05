#----------------------------------------------------------------------------------
#                       Check Licenses - shared module
#----------------------------------------------------------------------------------
# SCRIPT NAME:  CheckLicenses.py
#               v.2026.0303
#
# PURPOSE:      Checks for license availability.
#               Returns "yes" or "no" value and displays message.
#
# NOTES:        IMPORTANT NOTE FOR DEBUGGING - this script is imported to other
#               script tools.  If any edits to this script are done while an
#               ArcGISPro session is active, the changes made to this script will
#               not automatically apply.  You must save and close your ArcGISPro
#               session and start a new one in order to flush out the session's
#               memory.
#
# AUTHOR:       Julie Duval, fRI Research
#
# CREATED:      September 2011
#
# LAST UPDATES: March 3, 2026 (J. Duval)
#
# ---------------------------------------------------------------------------------
# SCRIPT FUNCTIONS:
#       main(args)          - Main function
#       CheckArcInfo()      - Checks for ArcInfo availability
#       CheckSpatialExt()   - Checks for Spatial Analyst availability
#       display(msg)        - Displays message as tool output message
#==================================================================================
import arcpy

class LicenseError(Exception):
    pass

class UnlicensedError(Exception):
    pass

#**********************************************************************************
#************************************ LICENSE CHECKS ******************************
#**********************************************************************************
def CheckArcInfo(go="yes"):
    #------------------------------------------------------------------------------
    'Function to checkout an ArcInfo level license'
    #------------------------------------------------------------------------------
    try:
        if arcpy.CheckProduct("ArcInfo") == "Available" or \
           arcpy.CheckProduct("ArcInfo") == "AlreadyInitialized":
            arcpy.SetProduct("ArcInfo")
            display("*** ArcInfo License is available")
        elif arcpy.CheckProduct("ArcInfo") == "NotLicensed":
            raise UnlicensedError
        else:
            raise LicenseError

    except UnlicensedError:
        display("*** Required ArcInfo license was not found.")
        go = "no"
    except LicenseError:
        display("*** ArcInfo license is unavailable and is required for this " +
                 "tool to run")
        go = "no"
    except:
        print(arcpy.GetMessages(2)); raise

    return (go)


def CheckSpatialExt(go="yes"):
    #------------------------------------------------------------------------------
    'Function to checkout a spatial analysit extension license'
    #------------------------------------------------------------------------------
    try:
        if arcpy.CheckExtension("spatial") == "Available":
            arcpy.CheckOutExtension("spatial")
            display("*** Spatial Analyst license is available")
        elif arcpy.CheckOutExtension("spatial") == "NotLicensed":
            raise UnlicensedError
        else:
            raise LicenseError

    except UnlicensedError:
        display("*** Required Spatial Analyst Extension license was not found.")
        go = "no"
    except LicenseError:
        display("*** Spatial Analyst license is unavailable and is required for "
                "this tool to run")
        go = "no"
    except:
        print(arcpy.GetMessages(2)); raise

    return (go)

def display(msg):
    arcpy.AddMessage(msg)
    print(msg)


def main():
    print("This module checks the availability of ArcGIS licenses and extensions.")


if __name__ == '__main__':
    main()
