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

## Setting up parameters in AWS SSM Parameter Store

This module expects that you have set up your parameters in the AWS SSM Parameter Store with a specific naming convention. The parameters should be named in the following format:

```
/{environment}/{project_name}/{parameter_name}
```
or, for parameters that will apply to all projects in an environment:
```
/{environment}/default/{parameter_name}
```

Default parameters will be loaded first, and merged with project-specific parameters. If a parameter exists in both locations, the project-specific parameter will take precedence.

## Loading parameters from a `yaml` file (for local development)

The `load_secure_settings()` function will also look for a `yaml` file in the same directory as the calling module named `secure.yaml`. If this file exists, it will be loaded and merged with the parameters from AWS SSM Parameter Store.