# Runoff calculation model
# David Gold
# August 2015
#
# Edited by Noah Warnke 2016
#
# Updated by Lisa Watkins 9/15/2016
#
# Edited by Tanvi Naidu 6/16/2017
#
# Based off of the runoff model created by Rebecca Marjerson in 2013
#
# Determine the runoff peak flow using the SCS curve number method (see TR-55 document for further details)
# 
# Inputs:   culvert_Q_input.csv: culvertID, watershed area (sq km), average curve number, time of concentration (hr)
#           ws_precip: csv file exported from the Cornell NRCC of 24 hour storms with return periods 1 to 500 years
#           rainfall_adjustment: scalar, with 1 as current rainfall.
#           output_filename: where to save the results of the runoff calculation.
#
# Outputs:  table of runoff (q_peak) in cubic meters per second for each return periods under current precipitation conditions
#           table of runoff (q_peak) in cubic meters per second for each return periods under future precipitation conditions

import numpy, os, re, csv, sys, loader
#Imports required packages and modules and the function 'loader' which was written
# in 2016 and saved as loader.py
#(loader organizes the data from input file based on headers defined in a signature)

def calculate(sorted_filename, watershed_precip_input_filename, rainfall_adjustment, output_filename):
    # Precipitation values (cm) are average for the overall watershed, for 24 hour storm, from NRCC
    # 1yr,2yr,5yr,10yr,25 yr,50 yr,100yr,200 yr,500 yr storm
    # Rainfall values are read directly from the standard NRCC output format and converted into cm.

    # Define signature for sorted watershed data input file.
    # This creates a list of dictionaries that stores the relevant headers of
    # the input file and the type of data in the column under that header
    watershed_data_signature = [
        {'name': 'BarrierID', 'type': str},
        #eg: The first element of the list 'watershed_data_signature' is a dictionary for barrier id.
        #'BarrierID' is the header of a column of data we want to extract from the input file,containing
        #data of type strings
        {'name': 'Area_sqkm', 'type': float},
        {'name': 'Tc_hr', 'type': float},
        {'name': 'CN', 'type': float}
        # Future: latitude and longitude and flags (aka number_of_culverts).
    ];

    # Define signature for watershed precipitation input file.
    precip_data_signature = [
        # Technically would be wise to also load the Freq (
        {'name': '24-hr', 'type': float}
    ];

    # Load and validate watershed data.
    # watershed_data will now store the relevant data from the culvert geometry input file
    # in the format described in loader.py using the signature defined above.
    # valid_rows will store all value for the key 'valid_rows' in the dictionary watershed_data
    watershed_data = loader.load(sorted_filename, watershed_data_signature, 1, -1)
    #Header in row 1, and we want to read all rows (max rows= -1)
    valid_watersheds = watershed_data['valid_rows']

    # Load precipitation data.
    precip_data = loader.load(watershed_precip_input_filename, precip_data_signature, 10, 9)
     #Header in row 10, and there are 9 rows to read (max rows= 9)
    precip_rows = precip_data['valid_rows']

    # If there is a problem loading the precipitation rows (i.e. less than 9 rows), bail out.
    if len(precip_rows) < 9:
        print "ERROR: failed to load all precipitation data from file '" \
            + watershed_precip_input_filename \
            + "'. Bailing out."
        sys.exit(0)

    # Create list of preciptations, converted to metric and adjusted.
    precips_list = []
    for row in precip_rows:
        precips_list.append(row['24-hr'] * 2.54 * rainfall_adjustment)
        #coverts from inches (nrcc default) to cm 

    # Clever multi-math technique: convert precips list to a vector aka array:
    P = numpy.array(precips_list)

    # Run the calculation for each watershed and each precipitation:
    results = []
    skipped_watersheds = []
    for watershed in valid_watersheds:

        #Store our watershed values in handy variables for calculations (from watershed dictionary)
        BarrierID = watershed['BarrierID']
        ws_area = watershed['Area_sqkm'] #sq km, calculated with ArcGIS tools 
        tc = watershed['Tc_hr'] #time of concentration in hours, calculated by ArcGIS script
        CN = watershed['CN'] #area-weighted average curve number

        # Skip over watersheds where curve number or time of concentration 
        # are 0 or watershed area < 0.01, since this indicates invalid data.
        # Note that this results in output files with potentially fewer 
        # watersheds in them than in the input file.
        if CN == 0:
            skipped_watersheds.append({'watershed': watershed, 'reason': 'CN = 0'})
            continue

        if tc == 0:
            skipped_watersheds.append({'watershed': watershed, 'reason': 'Tc_hr = 0'})
            continue

        if  ws_area < 0.01:
            skipped_watersheds.append({'watershed': watershed, 'reason': 'Area_sqkm < 0.01'})
            continue 
            
        # calculate storage, S  and Ia in cm
        Storage = 0.1 * ((25400.0 / CN) - 254.0) #cm
        Ia = 0.2 * Storage #inital abstraction, amount of precip that never has a chance to become runoff (cm)
    
        # calculate depth of runoff from each storm
        # if P < Ia NO runoff is produced
        # Note that P is a vector of the 9 values, so everything hereafter is too.
        Pe = (P - Ia) #cm
        Pe = numpy.array([0 if i < 0 else i for i in Pe]) # get rid of negative Pe's
        Q = (Pe ** 2) / (P + (Storage - Ia)) #cm

        
        #calculate q_peak, cubic meters per second
        # q_u is an adjustment because these watersheds are very small. It is a function of tc,
        # and constants Const0, Const1, and Const2 which are in turn functions of Ia/P (rain_ratio) and rainfall type
        # We are using rainfall Type II because that is applicable to most of New York State
        # rain_ratio is a vector with one element per input return period
        rain_ratio = Ia / P
        rain_ratio = numpy.array([.1 if i < .1 else .5 if i > .5 else i for i in rain_ratio])
        # keep rain ratio within limits set by TR55
        #Calculated
        Const0 = (rain_ratio ** 2) * -2.2349 + (rain_ratio * 0.4759) + 2.5273
        Const1 = (rain_ratio ** 2) *  1.5555 - (rain_ratio * 0.7081) - 0.5584
        Const2 = (rain_ratio ** 2) *  0.6041 + (rain_ratio * 0.0437) - 0.1761

        qu = 10 ** (Const0 + Const1 * numpy.log10(tc) + Const2 * (numpy.log10(tc)) ** 2 - 2.366)
        # qu would have to be m^3/s per km^2 per cm
        q_peak = Q * qu * ws_area #m^3/s
        #qu has weird units which take care of the difference between Q in cm and area in km2

        # Convert our vector back to a list and add the other info to the front.
        result = [BarrierID, ws_area, tc, CN] + q_peak.tolist()
        
        # Lastly, put our result for this watershed into the list of results.
        results.append(result)

    # Set up to save results to new file.
    with open(output_filename, 'wb') as output_file:
        csv_writer = csv.writer(output_file)

        # Header
        csv_writer.writerow(['BarrierID', 'Area_sqkm', 'Tc_hr', 'CN', 'Y1','Y2','Y5','Y10','Y25','Y50','Y100','Y200','Y500'])

        # Each row.
        # Later: when flags (aka number_of_culverts) is present, skip ahead that number
        # instead of just 1 in the results list (ie, ignore the second, third, etc. culvert.)
        for result in results:
            csv_writer.writerow(result)

    # output_file closed by with

    # Also save thrown-out watersheds into another file, if there were any.
    if len(skipped_watersheds) > 0:
        # TODO
        #Notifies user of skipped watersheds
        print "NOTE: skipped " \
            + str(len(skipped_watersheds)) \
            + " watersheds."

