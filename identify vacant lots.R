library(dplyr)
library(sf)
library(tidyr)
library(tidycensus)
#read in parcel_data

parcels<-st_read("Data Retrieval and Prep/parcel_data.geojson")%>%
  st_transform(crs="+init=epsg:4326")


vacant<-parcels%>%
  #limit to parcels over 30,000 sq feet
  filter(LOTAREA__asmt>=43560)%>%
  #limit to pittsburgh
  filter(PROPERTYCITY__asmt=="PITTSBURGH")%>%
  #limit to vacant parcels
  filter(USEDESC__asmt=="VACANT LAND")%>%
  #convert to centroid
  st_centroid()



#export files as geojson
st_write(vacant,"vacant_lots_centroid.csv",layer_options = "GEOMETRY=AS_XY")


