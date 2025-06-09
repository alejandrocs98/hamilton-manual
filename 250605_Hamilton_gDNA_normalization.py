#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 20 10:08:30 2017

@author: Susan Hromada
@date: August 2018
@purpose: gDNA_normalization.py reads an excel sheet containing concentrations of DNA in a 96 well plate and outputs a worklist for creating a 96 well plate of normalized gDNA
@note: EVO cannot pipette less than 3 uL
@update: Updated 2022_03_31 by Claire Palmer for use on the Fluent. I changed the write_worklist function so that the first aspirate command is from labware type 4 Deep Well_CMP, well 1 (left column). I also updated the reading in ODs portion to take an Excel sheet in the format I get when using the F200 attached to the Fluent.
@update: Updated 2022_09_14 by Claire Palmer, changed plate type for concentrated DNA
@update: Update 2022_09_20 by Claire Palmer, copied Susan's 8/03/22 edits from the other script into here

@update: Updated 2025_02_26 by Sarvesh Menon -> hm_gDNA_normalization.py, rehauled the code to work on for the Hamilton worklist format
"""

#%%#############################################################
#Inputs
############################################################
import argparse

parser = argparse.ArgumentParser(description="Normalize gDNA concentrations from Excel input for Hamilton worklist")
parser.add_argument('--excel', type=str, required=True, help='Path to Excel file with gDNA concentrations')
parser.add_argument('--tag', type=str, required=True, help='Name tag for output files')

args = parser.parse_args()

EXCEL_FILE_PATH = args.excel
NAME_TAG = args.tag

#path of quantIT excel template with concentration values
#EXCEL_FILE_PATH = "gDNA_concentrations_calculation_matrix_P1.xlsx"
#NAME_TAG = '250508_P1_normalized_gDNA'

#%%#############################################################
# Do not change anything below this line!!!!!!!!!!!!!!!!!!!!
###################################################################


#path to save your resulted worklist to
#WORKLIST_FILE_PATH = "250430_gDNA_concentrations_SUGs_worklist.csv"
WORKLIST_Water_FILE_PATH = NAME_TAG + "_water.csv"
WORKLIST_gDNA_FILE_PATH = NAME_TAG + "_gDNA.csv"

#path to save the actual concentrations output to
CONCENTRATIONS_OUTPUT_PATH = NAME_TAG + '_concentration.csv'

#water plate name, type and location(well?) 
water = ["Water","Source_plate_type",]

#plate type containing concentrated gDNA
PLATE_TYPE_START='RCK_CulturePlate_00'

#plate type you are normalizing into
PLATE_TYPE_NORM='RCK_PCRPlate_00'

#Do you want to plot gDNA concentration vs OD? If not, change this to False
plot=False
#location of OD data; this should be a single excel file in a folder with this name
OD_FILE_PATH = 'test_OD_data.xlsx' 
#path to save figure output
FIG_PATH='test_gDNAconc_OD.pdf'


import pandas as pd
import sys
sys.path.append('..')
import matplotlib.pyplot as plt

def load_sheet1(filename):
    # open the file
    xlsx = pd.ExcelFile(filename)
    
    # get the first sheet as an object
    sheet1 = xlsx.parse(0)
    
    return sheet1

def get_rows(sheet1, myrange):
    rows = []
    for i in myrange:
        row = sheet1.iloc[i]
        rows.append(row[1:])
       
    return rows

def plate_map(j,i):
     row_names = ["A","B","C","D","E","F","G","H"]
     col_ind = j+1
     row_ind = i
     
     new_ind = row_names[row_ind]+str(col_ind)
     return(new_ind)

#normalize_values() calculates the volume of gDNA (V1) needed using simple C1V1 = C2V2 equation
#norm_cutoff = desired normalized gDNA concentration (in ng/uL) (C2), often 2 ng/uL
#norm_volume = desired volume of normalized gDNA in normalized plate (in uL) (V2), often 50 uL
def normalize_values(rows, norm_cutoff, norm_volume):
    norm_values = []
    for i in range(0, len(rows)):
        row_norms = []
        for j in range(0, len(rows[i])):
            if rows[i][j] > norm_cutoff:
                volume = (norm_cutoff * norm_volume)/(float(rows[i][j]))
                row_norms.append(volume)
            else:
                row_norms.append(norm_volume)
        norm_values.append(row_norms)
    #returns the volume of gDNA (V1) needed for each well   
    return norm_values

#write_worklist() creates a .gwl worklist file containing pipetting steps to dilute gDNA of each well with H2O to a normalized concentration
#from 96 deep well plate to 96 microplate
#norm_values = volume of gDNA (V1) needed from each well, calculated by normalize_values()
#norm_volume = desired volume of normalized gDNA in normalized plate (in uL) (V2), often 50 uL
#worklist_filename = string ending in .gwl
def write_worklist(norm_values, norm_volume, worklist_water_file_path, worklist_gDNA_file_path):
    #worklist_file = open(worklist_filename,"w")
    concentration_file=open(CONCENTRATIONS_OUTPUT_PATH,'w+')
    
    #print("Worklist to pipette gDNA from 96 well deep well to 96 well microplate using volumes for Hamilton robot from gDNA concentrations excel")

    #Header line
    #worklist_file.write("Source_plate_Name,Source_Plate_Type,Source_Plate_Well,Desination_plate_Name,Destination_Plate_Type,Destination_Plate_Well,Transfer_Volume,Tip_Size,Liquid_class\n")
    worklist_water_df = pd.DataFrame()
    worklist_gDNA_df = pd.DataFrame()

    #write pipetting steps for each well to worklist
    for j in range(0, len(norm_values[0])): #each column
        for i in range(0,len(norm_values)):#each row
            gDNA_vol = int(round(norm_values[i][j]))
            gDNA_vol = max(gDNA_vol, 1) #line added by SEH on 8/3/2022
            water_vol = norm_volume - gDNA_vol
            #EVO cannot pipette less than 3 uL
            if (gDNA_vol == 2):
                gDNA_vol = 2*gDNA_vol
                water_vol = 2*water_vol
            if (gDNA_vol ==1):
                gDNA_vol = 3*gDNA_vol
                water_vol = 3*water_vol
            if (water_vol < 3 and water_vol != 0):
                gDNA_vol = norm_volume -3
                water_vol = 3
            #well_num = j*8 + i + 1
            #worklist_file.write(f"{water[0]},{water[1]},{plate_map(j,i)},96norm,{PLATE_TYPE_NORM},{plate_map(j,i)},{water_vol}\n")
            #worklist_file.write(f"96raw,{PLATE_TYPE_START},{plate_map(j,i)},96norm,{PLATE_TYPE_NORM},{plate_map(j,i)},{gDNA_vol}\n")
            new_row_water = pd.DataFrame({'Source_plate_Name':[water[0]],
                                          'Source_Plate_Type':[water[1]],
                                          'Source_Plate_Well':[plate_map(j,i)],
                                          'Desination_plate_Name':['96norm'],
                                          'Destination_Plate_Type':[PLATE_TYPE_NORM],
                                          'Destination_Well':[plate_map(j,i)],
                                          'Transfer_Volume':[water_vol],
					                      'Tip_Size':['300'],
					                      'Liquid_Class':['Water']})
            new_row_gDNA = pd.DataFrame({'Source_plate_Name':['96raw'],
                                         'Source_Plate_Type':[PLATE_TYPE_START],
                                         'Source_Plate_Well':[plate_map(j,i)],
                                         'Desination_plate_Name':['96norm'],
                                         'Destination_Plate_Type':[PLATE_TYPE_NORM],
                                         'Destination_Well':[plate_map(j,i)],
                                         'Transfer_Volume':[gDNA_vol],
                                         'Tip_Size':['300'],
                                         'Liquid_Class':['Water']})

            worklist_water_df = pd.concat([worklist_water_df, new_row_water], ignore_index=True)
            worklist_gDNA_df = pd.concat([worklist_gDNA_df, new_row_gDNA], ignore_index=True)
            

    #calculate resulting concentration for each well (due to rounding, etc, won't be precisely target conc)
    for i in range(0,len(norm_values)):#each row
        for j in range(0, len(norm_values[0])): #each column
            gDNA_vol = int(round(norm_values[i][j]))
            gDNA_vol = max(gDNA_vol, 1) #line added by SEH on 8/3/2022
            water_vol = norm_volume - gDNA_vol
            #EVO cannot pipette less than 3 uL
            #EVO cannot pipette less than 3 uL
            if (gDNA_vol == 2):
                gDNA_vol = 2*gDNA_vol
                water_vol = 2*water_vol
            if (gDNA_vol ==1):
                gDNA_vol = 3*gDNA_vol
                water_vol = 3*water_vol
            if (water_vol < 3 and water_vol != 0):
                gDNA_vol = norm_volume -3
                water_vol = 3
            actualconcentration=rows[i].iloc[j] * gDNA_vol / (water_vol + gDNA_vol)

            concentration_file.write(str(actualconcentration)+',')
        concentration_file.write('\n')
    #close files
    #worklist_file.close()
    concentration_file.close()
    worklist_water_df.to_csv(worklist_water_file_path, index=False)
    worklist_gDNA_df.to_csv(worklist_gDNA_file_path, index=False)
    #pd.concat([worklist_water_df, worklist_gDNA_df], ignore_index=True).to_csv(WORKLIST_FILE_PATH, index=False)
    

if plot:
	#Import OD600 Data
	ODDF = pd.read_excel(OD_FILE_PATH, header=None, names=['Well', 'OD'])

#enter path of quantIT data here (must be in standard quantIT data template)
sheet1 = load_sheet1(EXCEL_FILE_PATH)

#NOTE: THESE ROW NUMBERS ARE 2 LESS FROM WHAT IT READS IN EXCEL BC PANDAS IS WEIRD PLUS ZERO INDEXING
rows = get_rows(sheet1, range(28,36))

#columns 1-12 = 96 well plate
plate_rows = []
for i in range(0, len(rows)):
    tmp = []
    for j in range(0, len(rows[i])):
        tmp.append(rows[i].iloc[j])
    plate_rows.append(tmp)

#calculate volumes for normalization
norm_values = normalize_values(plate_rows, 2, 50)

#write worklists for normalization
write_worklist(norm_values, 50, WORKLIST_Water_FILE_PATH, WORKLIST_gDNA_FILE_PATH)

if plot:
	#Make scatter plot of OD600 versus gDNA concentration
	k=0
	for x in range(12):
		for y in range(8):
			plt.plot(ODDF.at[k,'OD'],rows[y][x],'bo')
			k+=1
	plt.xlabel('OD600')
	plt.ylabel('gDNA (ng/uL)')
	plt.savefig(FIG_PATH)
	plt.close()
