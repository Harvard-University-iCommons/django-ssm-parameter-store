import inspect
import logging
import os
import sys

import boto3
from botocore.exceptions import NoRegionError
import requests
import yaml


# for compatibility with YAML produced by ssm-diff:
class SecureYamlTag(yaml.YAMLObject, str):
    yaml_tag = u'!secure'

    @classmethod
    def from_yaml(cls, loader, node):
        return SecureYamlTag(node.value)


def load_secure_settings(project_name=None, environment=None):
    # returns a dict containing defaults overlaid with project-specific parameters

    # The ENV var must be set; fail otherwise
    if not environment:
        try:
            env = os.environ['ENV']
        except KeyError:
            try:
                # get the environment from an ec2 instance tag
                env = _get_env_from_ec2_tag()
            except:
                # raise an exception
                raise EnvironmentError('The ENV environment variable must be set or an ec2 tag "env" must be set.')

    caller_filename = inspect.stack()[1][1]
    # this is the path which contains the caller's module:
    caller_path = os.path.dirname(caller_filename)
    # this is the parent folder name of the caller's path
    caller_project_name = os.path.basename(os.path.dirname(caller_path))
    yaml_file = os.path.join(caller_path, 'secure.yml')

    if not project_name:
        if caller_project_name:
            project_name = caller_project_name
        else:
            raise EnvironmentError('Must provide a project_name.')

    config = {}

    try:
        _load_params_from_ssm(config, '/{}/defaults/'.format(env))
        _load_params_from_ssm(config, '/{}/{}/'.format(env, project_name))
    except:
        # could not load params from Parameter Store, but that may be ok
        pass

    # next try to overlay those parameters with values from a local file
    caller = inspect.stack()[1]
    try:
        yaml_params = yaml.load(open(yaml_file), Loader=yaml.Loader)
        _load_params_from_yaml(config, yaml_params, env, 'defaults')
        _load_params_from_yaml(config, yaml_params, env, project_name)
    except:
        # couldn't load params from a local file
        pass
    finally:
        del caller

    # sanity check:
    if len(config) == 0:
        raise Exception('No configuration values could be loaded from AWS SSM Parameter Store or a local file!')

    return config


def _load_params_from_yaml(config, yaml_params, env, namespace):
    try:
        for k in yaml_params[env][namespace]:
            config[k] = yaml_params[env][namespace][k]
    except KeyError:
        # couldn't load the parameters
        pass


def _load_params_from_ssm(config, path_prefix, region_name=None):
    # Load parameters from SSM Parameter Store starting with path.
    # Populate the config dict using keys from the path after the path_prefix
    if region_name:
        ssm = boto3.client("ssm", region_name=region_name)
    else:
        try:
            # try to use an externally-configured region
            ssm = boto3.client("ssm")
        except NoRegionError:
            # fall back to getting the region from instance metadata
            region_name = _get_region_from_metadata()
            ssm = boto3.client("ssm", region_name=region_name)
    args = {"Path": path_prefix, "Recursive": True, "WithDecryption": True}
    more = None
    while more is not False:
        if more:
            args["NextToken"] = more
        params = ssm.get_parameters_by_path(**args)
        for param in params["Parameters"]:
            keys = param['Name'][len(path_prefix):].split('/')
            _set_nested(config, keys, param['Value'])
        more = params.get("NextToken", False)


def _set_nested(dic, keys, value):
    # this sets a value in an arbitrarily-deeply nested dict
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def _get_env_from_ec2_tag():
    # first get the instance ID
    instance_details = requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document', timeout=1).json()

    ec2 = boto3.client('ec2', region_name=instance_details['region'])
    result = ec2.describe_tags(
        Filters=[
            {
                'Name': 'resource-id',
                'Values': [
                    instance_details['instanceId'],
                ],
            },
            {
                'Name': 'key',
                'Values': [
                    'environment',
                ],
            },
        ]
    )
    env = result['Tags'][0]['Value']
    return env


def _get_region_from_metadata():
    instance_details = requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document', timeout=1).json()
    return instance_details['region']