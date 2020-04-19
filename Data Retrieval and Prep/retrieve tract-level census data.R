library(dplyr)
library(tidyr)
library(readr)
#tidycensus requires a census api key: https://api.census.gov/data/key_signup.html
library(tidycensus)

vars<-load_variables(year=2018,dataset="acs5")


foot<-vars%>%
  filter(grepl("parcel",concept,ignore.case=TRUE))

#grab household income variables
income<-vars%>%
  filter(grepl("household income", concept,ignore.case=TRUE))

income<-vars%>%
  filter(grepl("B19001",name,ignore.case=TRUE))%>%
  mutate(label=gsub("!","",label),
         label=gsub("EstimateTotal","",label))
#label the first variable as total households
income$label[1]<-"Total Households"

#create named list of income variables to retrieve that will be fed into 
to_retrieve_income<-income$name[1:17]
names(to_retrieve_income)<-income$label[1:17]

#find car usage variables
car_vars<-vars%>%
  filter(grepl("car ", label, ignore.case=TRUE))
car_vars<-vars%>%
  filter(grepl("B08301",name,ignore.case=TRUE))

# create a named list of commute variables to retrieve
to_retrieve_commute<-c("Total Workers" = "B08301_001",
                       "Commute to work by car" = "B08301_002")
to_retrieve<-c(to_retrieve_income,to_retrieve_commute)

#retrieve data from census
pitt_census_vars<-get_acs(year=2018,variables=to_retrieve,state="PA",county = "Allegheny", geography="tract",geometry=TRUE)%>%
  #make data wide (one row per tract)
  select(GEOID,variable,estimate)%>%
  spread(key="variable",value="estimate")%>%
  #reorder variables
  select(c("GEOID",names(to_retrieve)))

write_csv(pitt_census_vars,"Alle Co income and commute census data.csv")
