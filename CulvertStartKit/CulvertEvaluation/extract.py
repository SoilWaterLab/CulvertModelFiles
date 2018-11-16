# Extract
# David Gold
# August, 14 2015
#
# This script will take the raw data collected in the field by either
# Fulcrum or NAACC data format and extracts useful information and assings
# Culvert ID numbers.

# Input: Field data csv downloaded from Fulcrum or the NAACC database
#
# Outputs: Culvert script input
#  EDITED Nov 2018 to save files in data folder, and to simplify input.
#   NOTE: raw data file MUST be saved in folder of the same name as the file
#       w/in CulvertEvaluation folder-  e.g. CulvertEvaluation/ALB/ALB.csv

ws_name=raw_input("Enter watershed abbreviation:")
data_type=raw_input("Fulcrum data or NAACC data? (Enter F for Fulcrum, N for NAACC):")
raw_data = ws_name + "/" + ws_name + ".csv"

#Make sure they can't input anything but F or N
while data_type !='f' and data_type != 'F' and data_type !='n' and data_type !='N':
    data_type=raw_input('Please enter either F for Fulcrum or N for NAACC:')

# Put the output files in the data folder you created
output=ws_name+"/"+ws_name+"_field_data.csv"
not_extracted=ws_name+"/"+ws_name+"_not_extracted.csv"
    
import numpy, os, re, csv

f_out = open(output, 'wb') #output file for extracted culverts
not_extracted_out= open(not_extracted, 'wb') #output for crossings not extracted
writer = csv.writer(f_out) #write object
writer_no_extract=csv.writer(not_extracted_out)

#write headings
writer.writerow(['BarrierID','NAACC_ID','Lat','Long','Rd_Name','Culv_Mat','In_Type','In_Shape','In_A','In_B','HW','Slope','Length','Out_Shape','Out_A','Out_B','Comments','Flags']) #header row
writer_no_extract.writerow(['Survey_ID','NAACC_ID','Lat','Long','Rd_Name','Culv_Mat','In_Type','In_Shape','In_A','In_B','HW','Slope','Length','Out_Shape','Out_A','Out_B','Comments','Flags']) #header row

# create an array to store field data values from the input spreadsheet
CD=[] # initialize an array to store field data values
for j in range(0,67):
    CD.append('blank')

with open(raw_data, 'r') as f:
    input_table = csv.reader(f)
    next(f) # skip header
    k=1
    if data_type=='F'or data_type=='f':
        for row in input_table: #each culvert 
            
                
                Fulcrum_ID=row[15]
                Lat=float(row[11])
                Long=float(row[12])
                Road_Name=row[16]
                
                # Assign culvert material and convert to language accepted by model
                Culv_material=row[18]
                if Culv_material=="Dual-Walled HDPE":
                    Culv_material="Plastic"
                elif Culv_material=="Corrugated HDPE":
                    Culv_material="Plastic"
                elif Culv_material=='Smooth Metal':
                    Culv_material='Metal'
                elif Culv_material=='Corrugated Metal':
                    Culv_material='Metal'
                
                Inlet_type=row[19]
                Inlet_Shape=row[22]               
                Inlet_A=float(row[23])
                Inlet_B=float(row[24])
                HW=float(row[25])
                Slope=float(row[26])
                Length=float(row[27])
                Outlet_shape=row[31]
                Outlet_A=float(row[34])
                Outlet_B=float(row[35])
                Comments=row[39]
                Fulcrum_ID
                Flags=0

                if Inlet_A<0:
                    next(f)
                elif Inlet_B<0:
                    next(f)
                elif HW<0:
                    next(f)
                elif Slope<0:
                    next(f)
                elif Length <1:
                    next(f)

                BarrierID=str(k)+ws_name
                k=k+1     
                writer.writerow([BarrierID, Fulcrum_ID, Lat, Long, Road_Name, Culv_material, Inlet_type, Inlet_Shape, Inlet_A, Inlet_B, HW, Slope,Length, Outlet_shape, Outlet_A, Outlet_B, Comments])
                           
    elif data_type=='N'or data_type=='n':
        NAAC_ID="1"   
        for row in input_table: #each culvert

            # eliminate blank cells from data and add data to array
            for i in range(0,62): 
                cell_value=row[i]
                if cell_value=='':
                    cell_value=-1
                CD[i]=cell_value # add field data to array

            BarrierID=str(k)+ws_name
            Survey_ID=CD[0]
            NAACC_ID=CD[35]
            Lat=float(CD[20])
            Long=float(CD[19])
            Road_Name=CD[26]
            Culv_material=CD[49]
            
            # Assign inlet type and then convert to language accepted by capacity_prep script
            Inlet_type=CD[22]
            if Inlet_type=="Headwall and Wingwalls":
                Inlet_type="Wingwall and Headwall"
            elif Inlet_type=="Wingwalls":
                Inlet_type='Wingwall'
            elif Inlet_type=='None':
                Inlet_type='Projecting'
                
            # Assign culvert shape and then convert to language accepted by capacity_prep script
            Inlet_Shape=CD[44]
            if Inlet_Shape=='Round Culvert':
                Inlet_Shape='Round'
            elif Inlet_Shape=='Pipe Arch/Elliptical Culvert':
                Inlet_Shape="Elliptical"
            elif Inlet_Shape=='Box Culvert':
                Inlet_Shape='Box'
            elif Inlet_Shape=='Box/Bridge with Abutments':
                Inlet_Shape='Box'
            elif Inlet_Shape=='Open Bottom Arch Bridge/Culvert':
                Inlet_Shape='Arch'
            
            Inlet_A=float(CD[47]) # Inlet_A = Inlet_Width
            Inlet_B=float(CD[43]) # Inlet B = Inlet Height
            HW=float(CD[27]) #This is from the top of the culvert, make sure the next step adds the culvert height
            Slope=float(CD[61]) 
            if Slope<0: # Negatives slopes are assumed to be zero
                Slope=0
            Length=float(CD[39])
            Outlet_shape=CD[55]
            Outlet_A=float(CD[58])
            Outlet_B=float(CD[54])
            Comments=CD[8]
            Number_of_culverts=float(CD[24])
            if Number_of_culverts > 1:
                if Number_of_culverts == 2:
                    Flags=2 # the crossing has two culverts
                elif Number_of_culverts == 3:
                    Flags=3 # The crossing has three culverts
                elif Number_of_culverts == 4:
                    Flags=4 # The crossing has four culverts
                elif Number_of_culverts == 5:
                    Flags=5 # The crossings has five culverts
                elif Number_of_culverts == 6:
                    Flags=6 # The crossing has six culverts
                elif Number_of_culverts == 7:
                    Flags=7 # The crossings has seven culverts
                elif Number_of_culverts == 8:
                    Flags=8 # The crossings has eight culverts
                elif Number_of_culverts == 9:
                    Flags=9 # The crossings has nine culverts
                elif Number_of_culverts == 10:
                    Flags=10 # The crossings has ten culverts                              
            else:
                Flags=0

            Neg_test=[Inlet_A,Inlet_B,HW,Length] # This step eliminates rows with negative values of Inlet_A, Inlet_B, HW, or Length from the analysis
            N=0
            for i in range(0,4):
                if Neg_test[i]<0:
                    N=N+1
                
            if CD[11]!="Bridge" and N==0:
                # Bridge crossings are not modeled
                # From Allison, 8/16/17: There are other types of crossings we do not model that are missed by this (e.g., ford, buried stream)
                writer.writerow([BarrierID, NAACC_ID, Lat, Long, Road_Name, Culv_material, Inlet_type, Inlet_Shape, Inlet_A, Inlet_B, HW, Slope,Length, Outlet_shape, Outlet_A, Outlet_A, Comments, Flags])
                k=k+1
            elif CD[44]=="Box/Bridge with Abutments" and Inlet_A<20 and N==0:
                # Bridge crossings less than 20 ft are considered culverts (question from Allison, 8/16/17: why do we not model Crossing_Type == Bridge AND Outlet_Type == Box Culvert?)
                writer.writerow([BarrierID, NAACC_ID, Lat, Long, Road_Name, Culv_material, Inlet_type, Inlet_Shape, Inlet_A, Inlet_B, HW, Slope,Length, Outlet_shape, Outlet_A, Outlet_A, Comments, Flags])
                k=k+1
            elif CD[44]=="Open Bottom Arch Bridge/Culvert" and Inlet_A<20 and N==0:
                # Bridge crossings less than 20 ft are considered culverts (see above question from Allison)
                writer.writerow([BarrierID, NAACC_ID, Lat, Long, Road_Name, Culv_material, Inlet_type, Inlet_Shape, Inlet_A, Inlet_B, HW, Slope,Length, Outlet_shape, Outlet_A, Outlet_A, Comments, Flags])
                k=k+1
            else:
                writer_no_extract.writerow([Survey_ID, NAACC_ID, Lat, Long, Road_Name, Culv_material, Inlet_type, Inlet_Shape, Inlet_A, Inlet_B, HW, Slope,Length, Outlet_shape, Outlet_A, Outlet_A, Comments, Flags])
            
f.close()
f_out.close()
not_extracted_out.close()

file_out_path=os.path.dirname(os.path.abspath(output))+'\\' + output
no_extract_out_path=os.path.dirname(os.path.abspath(not_extracted))+'\\' + not_extracted

print '\nExtraction complete! Exctracted values can be found here:\n'
print file_out_path
print 'Crossings excluded from analysis can be found here:\n'
print no_extract_out_path


                    
        
