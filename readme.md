# IBM i microservice demo using Python, fastAPI and Db2 with ODBC

Microservices are getting more and more popular, and ofcause 
you can develop microservies on the IBM i with python.

You have several options when it comes to which Python framework to use. I have used `Flask` - and you can find a demo on my git using that. However, `fastAPI` is getting more attetion these days for a number of reasons: it is simple to use, it is powerfull and it is .. fast ...

Another nice thing about `fastAPI` is the fact that it automatically provides the swagger interface for your service layer.

.. So let's get started:

# Your IBM i
In this project there are lots of references to `my_ibm_i` both in code, development tool and test.

This is of course the name of your IBM i. You can do yourself a favor and add the name `my_ibm_i` to 
your `hosts` file and let it point to the IP address of your IBM i - and all the code, 
development tool and test will work out of the box.

[Edit host file](https://www.howtogeek.com/howto/27350/beginner-geek-how-to-edit-your-hosts-file/)



# Setup the environment

I always use bash as my default shell. You can set that once and for all from ACS Run SQL script with: 

```
CALL QSYS2.SET_PASE_SHELL_INFO('*CURRENT', '/QOpenSys/pkgs/bin/bash');   
```

On IBM i you will need the open source in you path (and a nice prompt). So if you don't have a .profile yet, then:
```
ssh my_ibm_i
echo 'PATH=/QOpenSys/pkgs/bin:$PATH' >> $HOME/.profile
echo 'PS1="\h-\$PWD:\n"' >> $HOME/.profile
exit 
```

For the shell you can also click SSH Terminal in ACS or use a terminal like putty 

(or you can even use call qp2term – but I suggest that you get use to ssh)

From the terminal we need to install some open source tooling:

```
ssh my_ibm_i
yum install git
```

The data in this demo is provided by ODBC. First we can pull the yum part.

```
yum install ibm-iaccess
yum install unixODBC
yum install unixODBC-devel
```

It also requires the ODBC driver. Unfortunately you can
pull that directly from the IBM i yum repo - (as we speak - this might change)

You have to:
1) download the zip file where you get ACS
2) Unpack the zip file
3) move the *rpm* to the IBM i 
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
This shows the current configuration, that includes the configuration for your current IBM i - it is called ***LOCAL**

Now with the bould in command isql it is possible to run a
sql command: 

````
isql *LOCAL 
````

And then enter:

```sql
select * from qsys2.services_info
```

It will return a list of all IBM i db2 services available - and this is the list we will provide in our microservice demo in a moment.


## Next step: Install Python 


Our **fastAPI** microservice is coded in Python. So lets install that. Here we use version 3.9, and also notice that we install the python client to odbc:  

```
yum install python39
yum install python39-pyodbc
````


A nice trick is to setup a virtual python environment so you will not disturb other installations of Python on your IBM i. Here i put it into my project directory **/prj**. Perhaps consider to put in a more centralized place.

````
mkdir /prj
python3.9 -m venv --system-site-packages /prj/python39
source /prj/python39/bin/activate
````

Please note: Each time you reconnect to ssh, you need to switch to that virtual environment by:

```
source /prj/python39/bin/activate
````

Now we have python and and python package manager. Does it work? 

```
pip --version
python --version
```

## Next step: Install fastAPI python framework

Let's make a directory in our project folder for fastAPI and clone **this** git repo: 

```
mkdir /prj/fastAPI 
git -c http.sslVerify=false clone https://github.com/sitemule/ILEastic.git .
cd  /prj/fastAPI 
```

And then use the python package manger to install the required framework and tooling: 

```
pip install fastapi
pip install uvicorn
````

Here we install fastAPI - that is all the python code need for our microservice. 
fastAPI however depends on uvicorn - it is a cool server that also messures if
you change a source file, and if so-  reloads the application. that is quite
nice while you develop so you don't need to recycle your application by hand.

Lets try it out: The following code is called **hello.py**:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"} 

```

Now everything should be in place - you start the application with **uvicorn**. Does it work?

```
uvicorn hello:app --reload --port 60300 --host 0.0.0.0
```

From your browser you can now open our application

[http://my_ibm_i:60300](http://my_ibm_i:60300)


and we can examine the swagger interface from the **docs** page


[http://my_ibm_i:60300/docs] (http://my_ibm_i:60300/docs)


## The microservice

Until now we have "just" set up the python environment. Bringing it all together - Python, fastAPI and ODBC on IBM i is now possible. The current git repo contains also the **serviceInfo.py** that does exactly that. Lets see if it works: 

uvicorn servicesInfo:app --reload --port 60300 --host 0.0.0.0


.. amazing!! 

## The code:

```python
### First we need python to import ODBC and fastAPI 
import pyodbc
from fastapi import FastAPI, Query
from typing import Union

### We have two globals:
### The connection to our IBM i, and notice the *LOCAL. That is the default configuration  
connection =  pyodbc.connect("DSN=*LOCAL")

### the app is a name-space for all our fastAPI functionality 
app = FastAPI()

# Here is our real magic - Our primary endpoint:
# the @app.get will let fastAPI 
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


