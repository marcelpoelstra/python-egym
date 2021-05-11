# python-egym
A python interface into the eGym API

This project is forked from the apparently dormant (2017) project bitstacker/python-egym
I added new functions by sniffing the 2021 IOS e-gym app, and updated models.py and api.py accordingly.
Also fixed some minor issues in the models.

Tested on Ubuntu 20.10 and MacOS 11.3


To install and use :

- Check out this repository

- cd into the dir :  

 ```bash
 cd python-egym
 ```
- build using make :

``` bash
make

```
- install using pip :

``` bash
pip install -e .
```



## Example for use in your Python app:

```python
import egym

api = egym.Api(email='user@example.com',
                      password='userspassword')
print(api.GetUserProfile())
```
