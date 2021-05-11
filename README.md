# python-egym
A python interface into the eGym API

This project is forked from the apparently dormant (2017) project bitstacker/python-egym
I added new functions by sniffing the 2021 IOS e-gym app, and updated models.py and api.py accordingly.
Also fixed some minor issues in the models.




This api interface is inspired by python-twitter (https://github.com/bear/python-twitter).
If some api functions are missing, you are free to fork this project.

## How it works

```python
import egym

api = egym.Api(email='user@example.com',
                      password='userspassword')
print(api.GetUserProfile())
```
