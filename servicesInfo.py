import pyodbc
from fastapi import FastAPI, Query
from typing import Union

connection =  pyodbc.connect("DSN=*LOCAL")
app = FastAPI()

# Our primary endpoint:
# Usecase:
# http://my_ibm_i:60300/listServices?search=ptf
# http://my_ibm_i:60300/docs
@app.get("/listServices")
def listServices(search: Union[str, None] = Query(default=None, max_length=50)):
    sql = f'select * from qsys2.services_info where service_name like {string_quote("%" + search.upper() + "%")}'
    return fetch_all (connection , sql)

# Utility: 
# Returns a result-set produce by a SQL statement     
def fetch_all(connection , sql):
    c1 = connection.cursor()
    c1.execute(sql)
    ret = result_to_dict(c1)
    c1.close()
    return ret

# Utility:
# Converting a result-set to a dictionary that in turn will 
# be an JSON array with one object for each row 
def result_to_dict(cursor):
    try: 
        result = []
        columns = [to_camel_case(column[0]) for column in cursor.description]

        for row in  cursor.fetchall():
            result.append(dict(zip(columns,row)))
        if len(result) > 0:
            ret = result
        else:
            ret = {
                "error":True,
                "message": "no results found"
            }
    except pyodbc.Error as e:
        print(e)
        ret = { 
            "error":True,
            "message": "Internal Database Query Error",
            "reason" : e
        }
    
    return ret

# Utility:
# We capitalize the first letter of each component except the first one
# with the 'title' method and join them together.
def to_camel_case(snake_str):
    components = snake_str.lower().split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

# To avoid injection in SQL 
def string_quote (str):
    return "'" + str.replace("'","''") + "'" 
