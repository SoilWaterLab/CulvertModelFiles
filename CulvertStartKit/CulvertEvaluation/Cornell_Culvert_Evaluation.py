# Culvert Evaluation Model
# David Gold
# August 4, 2015
# These scripts are based on the culvert evaluation model developed by Rebecca Marjerison in 2013
#
# Object-oriented structure and resiliency updates built by Noah Warnke August 31 2016 (no formulas changed).
#
# Updated by Zoya Kaufmann June 2016 - August 2017
#
# Merged with older versions by Tanvi Naidu June 19 2017
#
# edited Nov 2018 by Jo Archibald to simplify file input
#
# This script will:
# 1. Determine the runoff peak discharge of given culvert's watershed using the SCS graphical curve number method.
# 2. Calculate the cross sectional area of each culvert and assign c and Y coefficients based on culvert characteristics
# 3. Determine the maximum capacity of a culvert using inlet control
# 4. Determine the maximum return period storm that the culvert can safely pass before overtopping for both current and
#    future rainfall conditions.
#
# Inputs:
# 1. Culvert Watershed data input: A CSV file containing data on culvert watershed characteristics including 
#    Culvert IDs, WS_area in sq km, Tc in hrs and CN

# 2. NRCC export CSV file of precipitation data (in) for the 1, 2, 5, 10, 25, 50, 100, 200 and 500 yr 24-hr storm events
#    Check that the precipitation from the 1-yr, 24 hr storm event is in cell K-11
#
# 3. Field data collection input: A CSV file containing culvert data gathered in the field using either then NAACC
#    data colleciton format or Tompkins county Fulcrum app
#
# Outputs:
# 1. Culvert geometry file: A CSV file containing culvert dimensions and assigned c and Y coefficients
#
# 2. Capacity output: A CSV file containing the maximum capacity of each culvert under inlet control
#
# 3. Current Runoff output: A CSV file containing the peak discharge for each culvert's watershed for
#    the analyzed return period storms under current rainfall conditions
#
# 4. Future Runoff output: A CSV file containing the peak discharge for each culvert's watershed for
#    the analyzed return period storms under 2050 projected rainfall conditions
#
# 5. Return periods output: A CSV file containing the maximum return period that each culvert can
#    safely pass under current rainfall conditions and 2050 projections.
#
# 6. Final Model ouptut: A CSV file that summarizes the above model outputs in one table

print('Cornell Culvert Evaluation Model')
print('--------------------------------\n')

#Importing required packages and modules and the function loader which was written
# in 2016 and saved as loader.py
#(loader organizes the data from input file based on headers defined in a signature)
import numpy, os, re, csv, runoff, capacity_prep, capacity, return_periods, time, sys, sorter, loader

#add note about making sure that the same culverts are in both sheets?

# 0. LOAD LIST OF COUNTY FILES

# Propmts user to input county file name, and corrects to proper '.csv' format
data_path = raw_input('Enter path folder containing this script and your data folder, for example: C:\Users\Tanvi\Desktop\Cornell_CulvertModel_StartKit_Nov2016\All_Scripts\: ')
check = raw_input('Master file called county_list.csv? Enter Y if correct, else enter correct file name')  # simplifies running a bit
if (check == "Y" or check == "y"):
    counties_filename = "county_list.csv"
else: counties_filename = check
# counties_filename = raw_input('Enter name of counties csv file in the Data folder: ')  # Removed Oct 2018

counties_filename = data_path + counties_filename
if counties_filename[len(counties_filename) - 4:] != '.csv':
    counties_filename = counties_filename + '.csv'  

# Signature for the county list csv file.
# This creates a list of dictionaries that stores the relevant headers of
# the input file and the type of data in the column under that header
counties_signature = [
    {'name': 'county_abbreviation', 'type': str},
    #eg: The first element of the list 'counties_signature' is a dictionary for 
    #county abbreviation. 'county_abbreviation' is the header of a column of data
    #we want to extract from the input file, containing data of type string
    {'name': 'watershed_data_filename', 'type': str},
    {'name': 'watershed_precipitation_filename', 'type': str},
    {'name': 'field_data_filename', 'type': str}
];

# Load and validate county file data.
# county_data will now store the relevant data from the counties csv input file
# in the format described in loader.py using the signature defined above.
# valid_rows will store all value for the key 'valid_rows' in the dictionary geometry_data
county_data = loader.load(counties_filename, counties_signature, 1, -1)
counties = county_data["valid_rows"]
invalid_counties = county_data["invalid_rows"]

# Notify of any invalid counties and exit if present.
if len(invalid_counties) > 0:
    print "\nERROR: Bailing out due to invalid county rows in '" + counties_filename + "':"
    for invalid in invalid_counties :
        print "* Row number " \
        + str(invalid["row_number"]) \
        + " was invalid because " \
        + invalid["reason_invalid"]
    sys.exit(0)

# For each county listed in the counties csv, perform all the computations:
for county in counties:
    # Grab the abbreviation and filenames from the county row.
    county_abbreviation = county["county_abbreviation"]
    #stores the values for key 'county_abbreviation' from dictionary 'county'
    watershed_data_input_filename = data_path + county["watershed_data_filename"]
    watershed_precip_input_filename = data_path + county["watershed_precipitation_filename"]
    field_data_input_filename = data_path + county["field_data_filename"]

    # Create filenames for all of the output files.
    output_prefix = data_path + county_abbreviation + "_"
    current_runoff_filename     = output_prefix + "current_runoff.csv"
    future_runoff_filename      = output_prefix + "future_runoff.csv"
    sorted_filename             = output_prefix + "sorted_ws.csv"
    culvert_geometry_filename   = output_prefix + "culv_geom.csv"
    capacity_filename           = output_prefix + "capacity_output.csv"
    return_period_filename      = output_prefix + 'return_periods.csv'
    final_output_filename       = output_prefix + 'model_output.csv'

    #Notifies user about runnign calculations
    print "\nRunning calculations for culverts in county " + county_abbreviation + ":"

    # 1. WATERSHED PEAK DISCHARGE
    
    # Sort watersheds so they match original numbering (GIS changes numbering)
    print " * Sorting watersheds by BarrierID and saving it to " + sorted_filename + "." 
    sorter.sort(watershed_data_input_filename, county_abbreviation, sorted_filename)

    # Culvert Peak Discharge function calculates the peak discharge for each culvert for current and future precip
    print " * Calculating current runoff and saving it to " + current_runoff_filename + "."
    runoff.calculate(sorted_filename, watershed_precip_input_filename, 1.0, current_runoff_filename)
    print " * Calculating future runoff and saving it to " + future_runoff_filename + "."
    runoff.calculate(sorted_filename, watershed_precip_input_filename, 1.15, future_runoff_filename) # 1.15 times the rain in the future.


    # 2. CULVERT GEOMETRY
    print " * Calculating culvert geometry and saving it to " + culvert_geometry_filename + "."
    # Culvert Capacity Prep function calculates the cross sectional area and assigns c and Y coeffs to each culvert
    capacity_prep.geometry(field_data_input_filename, culvert_geometry_filename)

    # 3. CULVERT CAPACITY
    print " * Calculating culvert capacity and saving it to " + capacity_filename + "."
    # Culvert_Capacities function calculates the capacity of each culvert (m^3/s) based on inlet control
    capacity.inlet_control(culvert_geometry_filename, capacity_filename)

    # 4. RETURN PERIODS AND FINAL OUTPUT
    print " * Calculating return periods and saving them to " + return_period_filename + "."
    print " * Calculating final output and saving it to " + final_output_filename + "."
    # Run return period script
    return_periods.return_periods(capacity_filename, current_runoff_filename, future_runoff_filename, return_period_filename, final_output_filename)

    ## TN, 2017: This step is no longer necessary since the final output is compiled in the return_periods.py script
    # 5. FINAL OUTPUT
    #print " * Calculating final output and saving it to " + final_output_filename + "."
    #Run final output script to aggregate all model outputs
    #final_output.combine(return_period_filename, capacity_filename, field_data_input_filename, watershed_data_input_filename, culvert_geometry_filename, final_output_filename)

print "\nDone! All output files can be found within the folder " + os.getcwd()

