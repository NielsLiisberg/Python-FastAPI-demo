import pyodbc
from fastapi import FastAPI

connection =  pyodbc.connect("DSN=*LOCAL")
app = FastAPI()


@app.get("/")
async def root():
    c1 = connection.cursor()
    c1.execute('select * from qiws.qcustcdt')
    return result2dict(c1)

def result2dict(cursor):
    try: 
        result = []
        columns = [column[0] for column in cursor.description]
        for row in  cursor.fetchall():
            result.append(dict(zip(columns,row)))
        if len(result) > 0:
            ret = result
        else:
            ret = {"message": "no results found"}
    except pyodbc.Error as e:
        print(e)
        ret = { "message": "Internal Database Query Error"}
    
    return ret