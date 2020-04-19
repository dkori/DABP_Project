library(dplyr)
library(sf)
library(tidyr)
library(tidycensus)
#read in parcel_data

parcels<-st_read("Data Retrieval and Prep/parcel_data.geojson")%>%
  st_transform(crs="+init=epsg:4326")



#read in census tracts from tidycensus
tracts<-get_acs(year=2018,variables=c("B01001_001"),
                geography="tract",
                state="PA",
                county="Allegheny",
                geometry=TRUE)%>%
  select(GEOID)%>%
  st_transform(crs="+init=epsg:4326")

parcels_with_geoid<-parcels%>%
  #create price per acre
  mutate(price_per_acre=LOCALLAND__asmt / (LOTAREA__asmt * 0.0000229568))%>%
  #convert to centroids of 
  st_centroid(of_largest_polygon=TRUE)%>%
  st_join(tracts,st_within,left=TRUE)

#add price per acres
parcels_with_value<-parcels_with_geoid%>%
  inner_join(parcels_with_geoid%>%
               #strip out the geometry (no longer needed)
               as.data.frame()%>%
               #calculate average price per census tract
               group_by(GEOID)%>%
               summarise(avg_price_per_acre=mean(price_per_acre,na.rm=TRUE))%>%
               ungroup())


vacant<-parcels_with_value%>%
  #limit to vacant parcels
  filter(USEDESC__asmt=="VACANT LAND")%>%
  #limit to parcels over 30,000 sq feet
  filter(LOTAREA__asmt>=30000)%>%
  #limit to pittsburgh
  filter(PROPERTYCITY__asmt=="PITTSBURGH")
#export files as geojson
st_write(parcels_with_value,"parcels_with_land_values.geojson")
st_write(vacant,"vacant_parcels_with_land_values.geojson")