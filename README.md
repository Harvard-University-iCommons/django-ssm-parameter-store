# django-ssm-parameter-store
This module retrieves environment-specific settings from from the AWS SSM Parameter Store at runtime.

## Basic usage:

```
from dj_secure_settings.loader import load_secure_settings

SECURE_SETTINGS = load_secure_settings()
```
With no arguments, the load_secure_settings() method will determine the environment by looking for an environment variable named `ENV`,
and it will determine the project name by using the grandparent-folder-name of the calling module.

You can explicitly pass values for either of these parameters to override the default behavior:
```
SECURE_SETTINGS = load_secure_settings(environment='dev', project_name='myproject')
```
