## load_uk_eso.py - grab company and daily records from the natgrid UK ESO API.

This is a program to grab records and information from company auctions from the UK ESO API and create and update a local database with those records.

This program will grab information from the [nationalgrid eso](https://www.nationalgrideso.com/) of the UK, filtered by date and company, and store the results to a local sqlite3 database.

## WHY I CREATED THIS
##

I worked with a company called Habitat Energy, who wanted to create daily database extractions and local storages of energy auctions from the national UK electric service provider. 
They would extract from the database every workday, but auctions would sometimes happen on weekends, so I expanded the original functionality, so that we could request a day or two behind. 
This program searches the API in O(n) time, though reasonably, it could be changed to Log(n) with a binary search of the API if later dates were to be sought after.

## INSTALLATION
##

1. `pip install -r requirements.txt`
   - `requests` is the only additional package
2. Run `python load_uk_eso.py`, or `python3 load_uk_eso.py` if running multiple versions

After that, you will be prompted to enter a set of parameters, such as resource_id, day, and company name, of which the defaults are:

resource_id = 'ddc4afde-d2bd-424d-891c-56ad49c13d1a'

day = present day

company name = 'HABITAT ENERGY LIMITED'

Setting the day far in the past will cause the program to run more slowly, as it starts by requesting recent entries and traverses towards records further in the past.
Conversely, setting the day slightly in the future (tomorrow) sometimes works faster, as the api forecasts records roughly a day in advance.
That said, this program is only designed to grab information from a day or two prior, never more than a month at any given time. I felt it was reasonable to take an O(n) linear approach for that purpose. 

## HOW IT WORKS
##

This program starts at the most recent entry to the results auction, and then filters down to a particular day. 
After that, it filters all of the results of the listed company, and saves them locally in a database. 
This program runs one company and date at a time, attempting to run more will cause faulty results or program error.

## REQUIREMENTS
##

This program requires the requests library from python, as well as sqlite3 for it's database loading. 
Other libraries used are sys and datetime.

run pip install requirements.txt if your local machine does not contain said modules.

## FUTURE DEVELOPMENTS
##

Given that this is a one-off script, I utilized global variables in order to adjust default parameters so we can search many different companies, dates, and resource id's dynamically. 
If this technology or script would be expanded, I would scrutinize and adapt this, such that I could maintain encapsulation for each of these functions. 
The global scope is present for this context, and this context only. Scope matters, encapsulation matters, and this context is the exception, not the norm. 
