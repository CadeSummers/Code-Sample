import requests
import sqlite3
from datetime import date, datetime
from sys import exit

base_url = 'https://data.nationalgrideso.com/api/3/action/datastore_search?'
offset='offset=100&'

#optional program to generate parameters for this search. default is listed
def generate_params():

    resource_id = 'resource_id=ddc4afde-d2bd-424d-891c-56ad49c13d1a'
    day = str(date.today())
    company = 'HABITAT ENERGY LIMITED'

    print(
'''
This program will grab the records for a company, date, and resource id from the API of the national grid electric service operator of the UK.
This program will use default parameters, unless specified otherwise.
Default parameters are:
-----------------------
''')

    print("Resource Id: " + resource_id[len('resource_id='):])
    print("Day (today by default): " + day)
    print("Company: " + company)

    in1 = input("Would you like to change these parameters? y/n?")

    if in1.lower() in ['y', 'yes']:

        in2 = input("Enter a new resource id or press enter to skip: ")

        if in2 not in ['\n', '']:
            print('You Entered: ' + in2)
            resource_id = resource_id[:len('resource_id=') - len(resource_id)] + in2

        in2 = input("WARNING: program searches most recent records to oldest records. Entering a past date more than a month before current day may cause a slow processing time.\nEnter a new day to search for or press enter to skip (format yyyy-mm-dd): ")
        
        if in2 not in ['\n', '']:
            print('You Entered: ' + in2)
            day = in2

        in2 = input("Enter a new company to search for or press enter to skip: ")

        if in2 not in ['\n', '']:
            print('You Entered: ' + in2)
            in2 = in2.upper()
            company = in2

    elif in1.lower() not in ['n', 'no', '']:
        print('Invalid input, please try again with y/yes/n/no inputs.')
        exit()

    return resource_id, day, company

#initial request to get the total number of entries. More recent entries are stored last, and initial entries are stored first
def init_req(init_url):

    print('Making initial request to API...')

    #request the initial page, and grab the total entries, and the date of the first day
    r = requests.get(init_url)
    data = r.json()
    total_entries = data['result']['total']
    first_day = data['result']['records'][0]['EFA Date']

    #if the day we input to check is before the first day, exit the program
    if datetime.strptime(first_day, '%Y-%m-%d') > target_date:
        print('Day inputted is before first known day of records: ' + first_day)
        exit()

    return total_entries

#request final entry page based on the offset_index, and traverse backwards until we find a purchase by habitat.energy on the same day as day
def find_current_day(offset_index):

    print('Finding records from date of input...')

    if str(day) != str(date.today()):
        print('Day inputted differs from present day. This may take longer than usual.')

    new_offset = 'offset='+str(offset_index)[:-2] + '00&'

    is_date = False

    while not(is_date):

        #establish this url to be searched
        url = base_url+new_offset+resource_id
        r = requests.get(url)
        data = r.json()

        #if the most recent record is before our selected date, exit the program
        if datetime.strptime(data['result']['records'][-1]['EFA Date'], '%Y-%m-%d') < target_date:
            print('Records of current date not yet added, try again at a later date.')
            exit()

        #grabs records from the api
        records = data['result']['records']

        for record in records:

            if record['EFA Date'] == day:
                is_date = True
                return offset_index, is_date
            
        if offset_index - 100 < 0:
            print('No record found for day')
            exit()
        offset_index-=100
        new_offset = 'offset='+str(offset_index)[:-2] + '00&'

#starting from the inputted day's url, traverse the records and either find the entries that include the company or break after passing the current date
def find_company_records(offset_index, is_date):

    print('Finding records for ' + str(company) + '...')
    
    company_records = []
    new_offset = 'offset='+str(offset_index)[:-2] + '00&'

    while is_date:
        
        url = base_url+new_offset+resource_id
        r = requests.get(url)
        data = r.json()
        records = data['result']['records']

        for record in records:

            #when the date of the record is the date before the record we've sought, we can exit the while loop
            if datetime.strptime(record['EFA Date'], '%Y-%m-%d') < target_date:
                is_date = False
                return company_records

            if record['Company'] == company:
                company_records.append(record)
            
        if offset_index - 100 < 0:
            print('No record found for day inputted. Search exhausted.')
            return

        offset_index-=100
        new_offset = 'offset='+str(offset_index)[:-2] + '00&'

#create a database, should need be
def create_db():

    db = sqlite3.connect('national_grid_eso.db')
    
    c = db.cursor()

    try:
        c.execute(""" CREATE TABLE natgrid_results (
            ID INTEGER,
            Company TEXT,
            Unit TEXT,
            Date TEXT,
            Delivery_Start TEXT,
            Deliver_End TEXT,
            EFA INTEGER,
            Service TEXT,
            Cleared_Volume INTEGER,
            Cleared_Price REAL,
            Technology TEXT,
            Location TEXT,
            Cancellation BOOL
        );""")

    #on table already existing, we can continue onwards
    except sqlite3.OperationalError:
        return
    db.commit()
    db.close()
    print("Database and table successfully created!")

def database_load(company_records):
    
    print('Loading to database...')
    
    db = sqlite3.connect('national_grid_eso.db')

    c = db.cursor()

    for record in company_records:

        #establish cancelled as a bool
        if record['Cancelled'] == '':
            record['Cancelled'] = False
        else:
            record['Cancelled'] = True

        #formatting database
        result_record = [(
            record['_id'],
            record['Company'],
            record['Unit Name'],
            record['EFA Date'],
            record['Delivery Start'],
            record['Delivery End'],
            record['EFA'],
            record['Service'],
            record['Cleared Volume'],
            record['Clearing Price'],
            record['Technology Type'],
            record['Location'],
            record['Cancelled']
        )]

        c.executemany("""INSERT INTO natgrid_results VALUES(
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        );""", result_record)

    db.commit()
    db.close()
           
def main():

    #establishing globals for easy access
    global day
    global company
    global resource_id
    global target_date
    resource_id, day, company = generate_params()
    target_date = datetime.strptime(day, '%Y-%m-%d')

    print("Finding results, this may take a few seconds...")

    init_url = base_url+offset+resource_id

    offset_index = init_req(init_url)

    offset_index, is_date = find_current_day(offset_index)

    company_records = find_company_records(offset_index, is_date)

    if len(company_records) == 0:
        print("No records found for given day")
        return

    print(str(len(company_records)) + " Records Found.")

    create_db()

    database_load(company_records)

    print("Program Success")
    print(str(len(company_records)) + " records loaded!")
    return

main()