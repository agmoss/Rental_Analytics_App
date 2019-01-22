# Standard library imports
import logging
import re
import functools
import time
from time import gmtime, strftime
import sys

# Third party imports
import mysql.connector
import schedule
import pandas as pd

# Local application imports
import scripts.Database as Database
import scripts.Accessor as Accessor
import scripts.Rental as Rental


""" Function wrappers for main() """

# Continue running if there is an exception in the main method
def catch_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            import traceback
            logging.info(traceback.format_exc())
            #return schedule.CancelJob  # Cancels the job if there is an exception
    return wrapper
    
# Logging decorator for scheduled function
def with_logging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info('LOG: Running job "%s"' % func.__name__)
        func(*args, **kwargs)
        logging.info('LOG: Job "%s" completed' % func.__name__)
    return wrapper

@catch_exceptions
@with_logging
def main():
    """
    Extract, Transform, Load

    Access each RentFaster.ca API page individually and store the results in MySQL. 

    Built in data cleaning, duplicate entry checking, database error handling, and scheduling.
    
    """

    logging.basicConfig(filename='app.log', filemode='w', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info('Start')

    i = 0 #Loop counter

    keys = [] # Primary Key List

    while True:

        try:

            page = str(i)

            url = 'https://www.rentfaster.ca/api/search.json?keywords=&proximity_type=location-proximity&cur_page=' + page + '&beds=&type=&price_range_adv[from]=null&price_range_adv[to]=null&novacancy=0&city_id=1'

            # Access object
            scr = Accessor.Accessor(url)

            data = scr.get_json()

            # There are multiple keys that can be accessed at this level, we want the listings data
            listings = data['listings']

            # We have reached the last page
            if len(listings) == 0:
                break
            
            # We have not reached the last page
            i += 1
                
            logging.info("Page " + page + " data obtained")

            # Connect to the database (exception raised if not connected)
            conn = Database.Database.connect()
            
            for listing in listings:

                try:

                    # Save Primary Key
                    keys.append(listing['ref_id'])

                    # Add retrieval date
                    listing['retrieval_date'] = pd.to_datetime('today').strftime("%m/%d/%Y")

                    # Add position
                    listing['position'] = "active"

                    # --- Data Cleaning ---

                    if 'sq_feet' in listing:
                        listing['sq_feet'] = re.sub("[^0-9]", "", listing['sq_feet'])
                    else:
                        listing['sq_feet'] = ""

                    if 'bedrooms' in listing:
                        listing['bedrooms'] = listing['bedrooms'].replace('bachelor', "0")
                    else:
                        listing['bedrooms'] = "0"
           
                    # Convert the list to a CSV string
                    if 'utilities_included' in listing:
                        listing['utilities_included'] = ",".join([str(x) for x in listing['utilities_included']]) 

                        # Remove whitespace 
                        listing['utilities_included'] = listing['utilities_included'].strip()

                        # Remove trailing comma
                        listing['utilities_included'] = listing['utilities_included'].rstrip(',')
                    else:
                        listing['utilities_included'] = ""

                    if 'den' not in listing:
                        listing['den'] = " "

                    if 'baths' not in listing:
                        listing['baths'] = " "

                    if 'cats' not in listing:
                        listing['cats'] = " "

                    if 'dogs' not in listing:
                        listing['dogs'] = " "

                    # --- End Data Cleaning ---

                    db = Database.Database.db_config()[3]
                    
                    # Instantiate Object
                    rental = Rental.Rental(listing["ref_id"],listing["userId"], listing["id"] ,listing["title"] ,listing["price"],listing["type"] ,
                    listing["sq_feet"],listing["availability"],listing["avdate"],listing["location"] ,listing["rented"] ,listing["thumb"] , listing["thumb2"] ,
                    listing["slide"] , listing["link"] ,listing["latitude"] , listing["longitude"],listing["marker"] ,listing["address"], listing["address_hidden"],  
                    listing["city"] ,listing["province"] , listing["intro"] , listing["community"] ,listing["quadrant"] , listing["phone"] , listing["phone_2"] ,
                    listing["preferred_contact"] ,listing["website"], listing["email"] , listing["status"] , listing["bedrooms"] , listing["den"] ,listing["baths"] , 
                    listing["cats"] , listing["dogs"] ,listing['utilities_included'], listing['position'], listing["retrieval_date"])

                    # Prepare a statement
                    statement = Database.Database.sql_writer_insert(db, list(rental.__dict__.keys()))

                    Database.Database.insert(conn, rental, statement) # exception NOT raised if data not inserted

                # Duplicate entry
                except mysql.connector.errors.IntegrityError as ie: # TODO: Custom raise

                    if ie.errno == 1062: # Duplicate entry
                        statement = Database.Database.sql_writer_update(db, list(rental.__dict__.keys()))
                        Database.Database.update(conn, rental, statement)

                except Exception as ex:
                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    logging.info(message)
                    continue

            conn.close()

        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logging.info(message)
            raise

        finally:
            logging.info("Page complete")

    logging.info("---All API data has been parsed and the database has been updated---")

    # Update rental listing status
    conn = Database.Database.connect() # Connect to the database (exception raised if not connected)

    Database.Database.key_status(conn, keys)

    logging.info("Bon Voyage")


if __name__ == "__main__":


    schedule.every().day.at("18:08").do(main)

    while True:
        sys.stdout.write("\r{0}".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
        sys.stdout.flush()
        schedule.run_pending()
        time.sleep(1)
    # TODO: Handle raised exceptions
    # TODO: Write tests
    # TODO: Notification of crash