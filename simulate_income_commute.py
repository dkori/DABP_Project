#Libraries
import pandas as pd
import censusgeocode as cg
import numpy as np
import random

## PARAMETERS ##
subset_size = 750
random_seed = 1234

#Load in the data
addresses = pd.read_csv("data/Allegheny_County_Address_Points.csv", na_values = [""])
census_tracts = pd.read_csv("data/census_variables.csv", na_values = ['NA', '-', '**'])
income_commute = pd.read_csv("data/Alle Co income and commute census data.csv")

#Remove useless columns from census_tracts
census_tracts = census_tracts.drop(columns = ["Unnamed: 0", "X"])

#Define a function for taking the address census_tract geocode

def get_info(df, address_col, state_col, zip_col, city_muni_col, subset_size, seed):
    '''
    Accepts a data frame and four strings specifying columns names where
    the full address, state, zip code, and city/municipality are stored.
    Any rows with NAs in these columns are filtered. The address attributes are
    extracted, and passed to censusgeocode to retrieve GEOID, which is added
    as a new column. A subset of rows of specified size is used with the 
    specified random seed.
    '''
    # Filter out any rows with NA in address related column
    f_df = df.dropna(subset = [address_col, state_col, zip_col, city_muni_col])
    
    #Select a random subset of rows to get addresses for
    #Dont need all of them for optimization
    subset_f_df = f_df.sample(n = subset_size, random_state = seed)
    
    #Initialize an empty list to collect the GEOIDs and latlon
    geoids = []
    lats = []
    lons = []
    
    #Takes a long to run, use a counter to check progress
    total_rows = len(subset_f_df)
    rows_complete = 0
    
    #iterate on each data frame row as a tuple, get address components
    for row in subset_f_df.itertuples():
        full_add = str(getattr(row, address_col))
        state = str(getattr(row, state_col))
        zip_code = str(int(getattr(row, zip_col)))
        city = str(getattr(row, city_muni_col))
        
        #Call censusgeocode for each row to get geoid
        result = cg.address(full_add, city = city, state = state, zipcode = zip_code)
        
        #If a match isn't found, geoid is np.NaN
        if len(result) == 0:
            geoid = np.NaN
            lat = np.NaN
            lon = np.NaN
        else:
            geoid = result[0]['geographies']['2010 Census Blocks'][0]['GEOID'][0:11]
            lat = result[0]['geographies']['2010 Census Blocks'][0]['INTPTLAT']
            lon = result[0]['geographies']['2010 Census Blocks'][0]['INTPTLON']
        
            #Clean the lat lon strings
            if lat[0] == '+':
                lat = float(lat[1:])
            else:
                lat = float(lat)
            
            if lon[0] == '+':
                lon = float(lon[1:])
            else:
                lon = float(lon)
        
        #Append to the frame
        geoids.append(geoid)
        lats.append(lat)
        lons.append(lon)
        
        rows_complete += 1
        
        #Report progress
        prog = round(rows_complete/total_rows, 4)
        print(prog*100,"%")
        
        
    
    #Append to the frame and return
    subset_f_df['GEOID'] = geoids
    subset_f_df['LATITUDE'] = lats
    subset_f_df['LONGITUDE'] = lons
    
    #Print the NaN Proportion
    nan_prop = subset_f_df['GEOID'].isna().sum()/total_rows
    print('Percent NaN GEOIDs:',nan_prop*100,'%')
    
    #Return the dataframe
    return subset_f_df

#Get the frame with GEOID
addresses = get_info(addresses, "FULL_ADDRESS", "STATE", "ZIP_CODE", "MUNICIPALITY", subset_size, random_seed)

# Force both GEOID columns to be int for joining
addresses['GEOID'] = addresses['GEOID'].astype(str)
income_commute['GEOID'] = income_commute['GEOID'].astype(str)

# Join the addresses result with income distribution
address_dist = addresses.merge(income_commute, how = "left", left_on = "GEOID", right_on = "GEOID")

# Filter rows with NAs in relevant columns
address_dist = address_dist.dropna(subset = ['GEOID', 'LATITUDE', 'LONGITUDE', 
       'Total Households', 'Less than $10,000', '$10,000 to $14,999',
       '$15,000 to $19,999', '$20,000 to $24,999', '$25,000 to $29,999',
       '$30,000 to $34,999', '$35,000 to $39,999', '$40,000 to $44,999',
       '$45,000 to $49,999', '$50,000 to $59,999', '$60,000 to $74,999',
       '$75,000 to $99,999', '$100,000 to $124,999', '$125,000 to $149,999',
       '$150,000 to $199,999', '$200,000 or more', 'Total Workers',
       'Commute to work by car'])

# Create functions to model income and commute probality based on census distributions
def sim_income_commute(df):
    '''
    Simulates income for a data frame based on census income bins.
    '''
    #initialize empty lists
    incomes = []
    commute_statuses = []
    
    for row in df.itertuples():

        #Get the proper attributes
        households = int(getattr(row, "_41"))
        lt_10k = int(getattr(row, "_42"))
        _10_to_14_999 = int(getattr(row, "_43"))
        _15_to_19_999 = int(getattr(row, "_44"))
        _20_to_24_999 = int(getattr(row, "_45"))
        _25_to_29_999 = int(getattr(row, "_46"))
        _30_to_34_999 = int(getattr(row, "_47"))
        _35_to_39_999 = int(getattr(row, "_48"))
        _40_to_44_999 = int(getattr(row, "_49"))
        _45_to_49_999 = int(getattr(row, "_50"))
        _50_to_59_999 = int(getattr(row, "_51"))
        _60_to_75_999 = int(getattr(row, "_52"))
        _75_to_99_999 = int(getattr(row, "_53"))
        _100_to_124_999 = int(getattr(row, "_54"))
        _125_to_149_999 = int(getattr(row, "_55"))
        _150_to_199_999 = int(getattr(row, "_56"))
        gr_200k = int(getattr(row, "_57"))
        total_workers = int(getattr(row, "_58"))
        com_by_car = int(getattr(row, "_59"))
        
        #Simulate income
        #randomly generate a number between 1 and the total households
        #See what bracket that falls into and uniformly generate the income
        samples = [i for i in range(1, households+1)]
        x = random.sample(samples, 1)[0]
        
        #Sampling pointer
        s = 0
        
        if 1 <= x <= lt_10k:
            income = int(random.uniform(1, 9999))
        
        s += lt_10k
            
        if s < x <= (_10_to_14_999+s):
            income = int(random.uniform(10000, 14999))
            
        s += _10_to_14_999
        
        if s < x <= _15_to_19_999+s:
            income = int(random.uniform(15000, 19999))
            
        s += _15_to_19_999
        
        if s < x <= _20_to_24_999+s:
            income = int(random.uniform(20000, 24999))
            
        s += _20_to_24_999
        
        if s < x <= _25_to_29_999+s:
            income = int(random.uniform(25000, 29999))
            
        s + _25_to_29_999
            
        if s < x <= _30_to_34_999+s:
            income = int(random.uniform(30000, 34999))
            
        s += _30_to_34_999
            
        if s < x <= _35_to_39_999+s:
            income = int(random.uniform(35000, 39999))
            
        s += _35_to_39_999
        
        if s < x <= _40_to_44_999+s:
            income = int(random.uniform(40000, 44999))
            
        s += _40_to_44_999
            
        if s < x <= _45_to_49_999+s:
            income = int(random.uniform(45000, 49999))
            
        s += _45_to_49_999
            
        if s < x <= _50_to_59_999+s:
            income = int(random.uniform(50000, 59999))
            
        s += _50_to_59_999
        
        if s < x <=  _60_to_75_999+s:
            income = int(random.uniform(60000, 74999))
            
        s += _60_to_75_999
            
        if s < x <=  _75_to_99_999+s:
            income = int(random.uniform(75000, 99999))
            
        s += _75_to_99_999
            
        if s < x <=  _100_to_124_999+s:
            income = int(random.uniform(100000, 124999))
            
        s += _100_to_124_999
            
        if s < x <=  _125_to_149_999+s:
            income = int(random.uniform(125000, 149999))
            
        s += _125_to_149_999
            
        if s < x <=  _150_to_199_999+s:
            income = int(random.uniform(150000, 199999))
            
        s += _150_to_199_999
            
        if s < x <=  gr_200k+s:
            income = int(random.uniform(200000, 250000))
        
        incomes.append(income)
        
        #Simulate commute status
        #Assume independence from income, except at the highest and lowest levels
        
        if income <= 15000:
            commute = 0
        
        elif income >= 100000:
            commute = 1
        
        else:
            prob_commute = com_by_car / total_workers
            commute = np.random.choice([1,0], 1, p = [prob_commute, 1-prob_commute])[0]
        
        commute_statuses.append(commute)
        
        #Return the resulting lists as a tuple
    return incomes, commute_statuses

#Run the function on our data frame
incomes_list, commute_statuses = sim_income_commute(address_dist)

#Append to the frame
address_dist['simulated_income'] = incomes_list
address_dist['simulated_commute_car'] = commute_statuses

#Get the relevant columns and write to CSV
cols = ['GEOID','FULL_ADDRESS', 'MUNICIPALITY', 'COUNTY', 'STATE', 'ZIP_CODE', 'LATITUDE', 'LONGITUDE', 'simulated_income', 'simulated_commute_car']
final_df = address_dist[cols]

#Print NA sums in the final results
print('Total NA values in final CSV:')
print(final_df.isna().sum().sum())

final_df.to_csv('addresses_simulated_incomes.csv', index = False)