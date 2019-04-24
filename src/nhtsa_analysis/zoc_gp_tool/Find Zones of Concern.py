# coding: utf-8
# #############
"""
Tool Name:  Query time from a datetime field
Source Name: FindPipelineWaterCrossings.py
Version: ArcGIS Pro 2.3
Author: Alberto Nieto, Esri

This tool .
"""

################### Imports ########################
import os as OS
import sys as SYS
import collections as COLL
import numpy as NUM
import datetime as DT
import arcpy as ARCPY
import arcpy.management as DM
import arcpy.da as DA
import ErrorUtils as ERROR
import SSUtilities as UTILS
import SSDataObject as SSDO
import locale as LOCALE
LOCALE.setlocale(LOCALE.LC_ALL, '')

# import arcpy

################### GUI Interface ###################

def setupFindPipelineWaterCrossings():
    """Retrieves the parameters from the User Interface and executes the
    appropriate commands."""

    workspace = ARCPY.GetParameterAsText(0)
    route_features = ARCPY.GetParameterAsText(1)
    route_id_field = 

    input_route_features = arcpy.GetParameterAsText(0)
    input_hydrology_features = arcpy.GetParameterAsText(1)
    output_fc = ARCPY.GetParameterAsText(2)
    crossing_distance_thresh = ARCPY.GetParameterAsText(3)
    from_field = UTILS.getTextParameter(4, fieldName = True)
    to_field = UTILS.getTextParameter(5, fieldName = True)   

    ssdo = SSDO.SSDataObject(input_route_features, templateFC = outputFC,
                             useChordal = False)

    ssdo.obtainData(ssdo.oidName, fieldList, minNumObs = 1) 

    mc = MeanCenter(ssdo, weightField = weightField, 
                    caseField = caseField, dimField = dimField)

    mc.createOutput(outputFC)

# Establish general variables that will be determined by the user as input parameters

route_features = ""
hydrology_features = ""
hydrology_event_from_field = "FMEAS"
hydrology_event_to_field = "TMEAS"

crossing_distance_thresh = 100  # Measured in the units of the input route referencing units (feet for PHMSA purposes)

class PipelineWaterCrossings(object):

    """This tool identifies the water crossing events along a pipeline route.

    INPUTS: 
    workspace (str): path to file geodatabase to be used as a workspace
    route_features (str): path to the input pipeline route feature class
    route_id_field (str): name of route identification field in route_features
    hydrology_features (str): path to the input hydrology polygonal feature class
    output_fc_name (str): name of the output feature class
    output_route_id_field (str): name of output route identification field
    output_event_from_field (str): name of from measurement field
    output_event_to_field (str): name of to measurement field
    crossing_distance_tresh (double): water crossing distance for output events

    ATTRIBUTES:

    METHODS:

    NOTES:
    """

    arcpy.env.overwriteOutput = True

    # Set a path to the event table output to be created in the workspace
    arcpy.AddMessage("Setting event table path...")
    event_table_path = os.path.join(workspace, "water_crossing_events")

    arcpy.AddMessage("Setting output field params...")
    # Set a variable for the parameter needed for the geoprocessing tools containing output field designation
    output_field_param = "{0} {1} {2} {3}".format(str(output_route_id_field),
                                                  "Line",
                                                  str(output_event_from_field),
                                                  str(output_event_to_field))

    # Set a variable for the event layer name
    event_layer_name = "Pipeline Water Crossing Events"
    event_layer_mdelta_field = "meas_delta"

    # Geoprocessing tool - Locate Features Along Routes - When using the NHDArea dataset, creates an event table
    # containing intersection between pipeline routes and the NHDArea polygonal features.
    arcpy.AddMessage("Locating hydrological features along pipeline routes (this operation may take some time)...")
    arcpy.lr.LocateFeaturesAlongRoutes(
        hydrology_features,
        route_features,
        route_id_field,
        "0 DecimalDegrees",
        event_table_path,
        output_field_param,
        "FIRST", "DISTANCE", "ZERO", "FIELDS", "M_DIRECTON"  # Default runtime params
    )

    arcpy.AddMessage("Creating event layer...")
    arcpy.lr.MakeRouteEventLayer(
        route_features,
        route_id_field,
        event_table_path,
        output_field_param,
        event_layer_name,
        None, "NO_ERROR_FIELD", "NO_ANGLE_FIELD", "NORMAL", "ANGLE", "LEFT", "POINT"  # Default runtime params
    )

    arcpy.AddMessage("Adding measurement delta field...")
    # Add a new field to the event layer to contain the measurement deltas
    arcpy.AddField_management(event_layer_name, event_layer_mdelta_field, "DOUBLE")

    # with arcpy.da.UpdateCursor(event_layer_name, event_layer_mdelta_field)

    arcpy.AddMessage("Calculating measurement deltas...")
    arcpy.management.CalculateField(
        event_layer_name,
        event_layer_mdelta_field,
        "!{0}! - !{1}!".format(str(output_event_to_field), str(output_event_from_field)),
        "PYTHON_9.3",
        None)

    arcpy.AddMessage("Selecting and exporting water crossings that surpass the crossing distance threshold...")
    arcpy.management.SelectLayerByAttribute(
        event_layer_name,
        "NEW_SELECTION",
        "{0} >= {1}".format(str(event_layer_mdelta_field), str(crossing_distance_thresh))
        )

    arcpy.management.CopyFeatures(
        event_layer_name,
        output_fc_name,
        None, None, None, None)

    arcpy.AddMessage("Output feature class: {0}".format(str(output_fc_name)))

    arcpy.AddMessage("Operation Completed.")


if __name__ == "__main__":
    setupFindPipelineWaterCrossings()
