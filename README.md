# python-egym
A python interface into the eGym API

This api interface is inspired by python-twitter (https://github.com/bear/python-twitter).
If some api functions are missing, you are free to fork this project.

## How it works

```python
import egym

api = egym.Api(email='user@example.com',
                      password='userspassword')
print(api.GetUserProfile())
```
