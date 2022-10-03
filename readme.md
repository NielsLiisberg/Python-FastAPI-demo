# IBM i microservice demo using Python, FastAPI and Db2 with ODBC

Microservices are getting more and more popular, and of cause
you can develop microservices on the IBM i with Python .

You have several options when it comes to which Python  framework
to use. I have used `Flask` - and you can find a demo on my git
using that. However, `FastAPI` is getting more attention these
days for a number of reasons: it is simple to use, it is powerful
and it is .. fast ...

Another nice thing about `FastAPI` is the fact that it 
automatically provides the swagger interface for your service layer.

.. So let's get started:

# Your IBM i
In this project there are lots of references to `my_ibm_i` both in 
code, development tool and test.

This is of course the name of your IBM i. You can do yourself a favor 
and add the name `my_ibm_i` to 
your `hosts` file and let it point to the IP address of your IBM i - 
and all the code, 
development tool and test will work out of the box.

[Edit host file](https://www.howtogeek.com/howto/27350/beginner-geek-how-to-edit-your-hosts-file/)



# Setup the environment

I always use `bash` as my default shell. You can set that once and for 
all from ACS Run SQL script with: 

```
CALL QSYS2.SET_PASE_SHELL_INFO('*CURRENT', '/QOpenSys/pkgs/bin/bash');   
```

On IBM i you will need the open source in you path (and a nice prompt). 
So if you don't have a `.profile` file yet, then:
```
ssh my_ibm_i
echo 'PATH=/QOpenSys/pkgs/bin:$PATH' >> $HOME/.profile
echo 'PS1="\h-\$PWD:\n"' >> $HOME/.profile
exit 
```

For the shell you can also click SSH Terminal in ACS or use a terminal
like `putty` 

(or you can even use call qp2term – but I suggest that you get use to ssh)

## Install git 
From the terminal we need to install some open source tooling. To 
pull this project you first of all need the git client on your IBM i.


```
ssh my_ibm_i
yum install git
```

.. And from now on, i assume you are keeping the ssh terminal open. So I will lave out the `ssh my_ibm_i`. 

## Install ODBC
The data in this demo is provided by ODBC. First we can pull the yum part.

```
yum install ibm-iaccess
yum install unixODBC
yum install unixODBC-devel
```

It also requires the ODBC driver. Unfortunately you can
pull that directly from the IBM i yum repo - (as we speak - this might change)

You have to:
1) Download the zip file where you get ACS
2) Unpack the zip file
3) Move the *rpm* to the IBM i 
4) Finally *yum* the *rpm*. 

This is described much better here: 

https://www.ibm.com/support/pages/odbc-driver-ibm-i-pase-environment
https://techchannel.com/SMB/08/2019/ODBC-Driver-for-IBM-i
https://ibmi-oss-docs.readthedocs.io/en/latest/odbc/using.html


With all this in place. Now let's test if the ODBC works:

Lets look at the ODBC configuration:
```
odbcinst -j
```
This shows the current configuration. Notice that includes the configuration for your current IBM i - it is called `*LOCAL`

Now with the builtin command `isql` it is possible to run a
sql command: 

````
isql *LOCAL 
````

And then enter:

```sql
select * from qsys2.services_info
```

It will return a list of all IBM i db2 services available - and 
this is the list we will provide in our microservice demo in a moment.


## Next step: Install Python  


Our `FastAPI` microservice is coded in Python . So lets install that. Here we use version 3.9, and also notice that we install the Python client to odbc:  

```
yum install python39
yum install python39-pyodbc
````


A nice trick is to setup a virtual Python environment so you will 
not disturb other installations of Python on your IBM i. Here i put it
into my project directory `/prj`. Perhaps consider to put in a more
centralized place.

````
mkdir /prj
python3.9 -m venv --system-site-packages /prj/python39
source /prj/python39/bin/activate
````

Please note: Each time you reconnect to ssh, you need to switch to that virtual environment by:

```
source /prj/python39/bin/activate
````

Now we have Python and and Python package manager. Does it work? 

```
python --version
pip --version
```

## Next step: Install the Python code

Let's make a directory in our project folder for FastAPI and clone `this` git repo to our IBM i: 

```
mkdir /prj/FastAPI 
cd  /prj/FastAPI
git -c http.sslVerify=false clone https://github.com/NielsLiisberg/Python-FastAPI-demo.git .
```

And then use the Python package manger to install the required framework and tooling: 

```
pip install fastapi
pip install uvicorn
````

Here we install FastAPI - that is all the Python code need for our microservice. 
FastAPI however depends on uvicorn - it is a cool server that 
also measures if
you change a source file, and if so-  reloads the application. that is quite
nice while you develop so you don't need to recycle your application by hand.

Lets try it out: The following code is called `hello.py` in the repo:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"} 

```

Now everything should be in place - you start the application with `uvicorn`. Does it work?

```
uvicorn hello:app --reload --port 60300 --host 0.0.0.0
```

From your browser you can now open our application

[http://my_ibm_i:60300](http://my_ibm_i:60300)


and we can examine the swagger interface from the `docs` page


[http://my_ibm_i:60300/docs] (http://my_ibm_i:60300/docs)

## The code

Well, the `hello.py` does not look of much. However it is magic: 

1) first we let Python include our FastAPI framework
2) The `@app.get("/")` routes any http `GET` request to call the method `root`
3) Here we simply returns a JSON object asynchronously  
4) `uvicorn` now runs the Python code

... we have a service :)



## The microservice

Until now we have "just" set up the Python environment. It is now possible to bringing it all together - Python, FastAPI and ODBC on IBM i . The current git repo contains also the `serviceInfo.py` that does exactly that. Lets see if it works: 

```
uvicorn servicesInfo:app --reload --port 60300 --host 0.0.0.0
```

.. amazing!! 

## The code:

```python
### First we need Python to import ODBC and FastAPI 
import pyodbc
from fastapi import FastAPI, Query
from typing import Union

### We have two globals:
### 1) The connection to our IBM i, and notice the *LOCAL. That is the default configuration  
connection =  pyodbc.connect("DSN=*LOCAL")

### 2) the app is a name-space for all our FastAPI functionality 
app = FastAPI()

# Here is our real magic - Our primary endpoint:
# the @app.get will let FastAPI 
# "route" any http GET operation with the name of "listServices"   
# whatever we "return" from this method goes to the browser.
# Note the "search" it will be shown in swagger as a query parameter of string of length 50  
# Use-case:
# http://my_ibm_i:60300/listServices?search=%PTF%
# http://my_ibm_i:60300/docs
@app.get("/listServices")
def listServices(search: Union[str, None] = Query(default=None, max_length=50)):
    sql = f'select * from qsys2.services_info where service_name like {string_quote(search)}'
    return fetch_all (connection , sql)

# The rest of the code is basically boilerplate that could go into 
# a separate generic file or be replaced by a framework.
# I have just implemented it for simplicity  

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

```



