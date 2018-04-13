#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
###
#
# Install the latest Datadog process agent.
#
###

import logging
logger = logging.getLogger(__name__)

import platform
import yum
import os,re
from shutil import copyfile
from jinja2 import Environment, FileSystemLoader
import json

#
### Get the API key for dd
local_config_path = os.path.abspath('conf')
local_json_config = local_config_path+"/config.json"
logger.info("Load the local config to get the dd api key")
with open(local_json_config, 'r') as f:
  config = json.load(f)

api_key = config['DEFAULT']['dd_api_key']
logger.info("the API to be used: api_key")
###
#


DD_AGENT_CONF_TEMPL_NAME = 'dd-process-agent.ini.templ'
PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
  autoescape=False,
  loader=FileSystemLoader(os.path.join(PATH, 'templates')),
  trim_blocks=False
 )

# Render it
def render_template(
  template_filename,
  context
):
  """
  Renders the template file with jinja2

  * template_filename:  The name of the template to use.
  * context:            the values to be interpolated in the tempalte
  """
  return TEMPLATE_ENVIRONMENT.get_template(template_filename).render(context)


def create_config(
  dd_api_key,
  host_name,
  templ_name=None
):
  """
  Create a local rendered config from the template file.

  * dd_api_key:       The api key for our data dog account.
  * host_name:        The host name of this system that is being registered with
                      Data dog
  * templ_name:       the name of the dd agents config template to use to render
  """

  if templ_name is None:
      templ_name=DD_AGENT_CONF_TEMPL_NAME

  fname = "/etc/datadog-agent/dd-process-agent.ini"
  valuse = [
    dd_api_key,
    host_name
  ]

  context = {
    dd_api_key  = 'dd_api_key'
    host_name   = 'host_name'
    }

  logger.info("loading the config: %s file from the template: %s" % (fname,templ_name))
  with open(fname, 'w') as f:
    config = render_template(templ_name, context)
    f.write(config)
  return fname

########################
#
### Copy's the config from the "files" directory and puts it into place.
try:
  logger.info("Copying the repo file into place.")
  src_path  = os.path.abspath('files')
  src       = src_path+"/datadog-process.repo"
  dst       = '/etc/yum.repos.d/datadog-process.repo'
  copyfile(src, dst)
except:
  logger.error("Could not copy the repo file into place")

### Install the agent software from the new dd-agent repo
try:
  logger.info("Installing the new dd-agent.")
  yb=yum.YumBase()
  searchlist=['name']
  arg=['dd-process-agent']
  matches = yb.searchGenerator(searchlist,arg)
  for (package, matched_value) in matches :
    if package.name == 'dd-process-agent':
      yb.install(package)
    yb.buildTransaction()
    yb.processTransaction()
except:
  logger.error("could not install the package from the new repo.")


host_name = platform.node()
### Create the DataDog process agent config
try:
  logger.info("putting the dd-process-agent config in place.")
  create_config(api_key,host_name)
except:
  logger.error("Could not create the config file: dd-process-agent.ini")

### start the process.
# check the version:
system_version = platform.linux_distribution()[1].rsplit('.')[0]
try:
  logger.info("starting the dd-process-agent")
  if system_version == '6':
    subprocess.call(["service", "dd-process-agent", "start"])
  elif system_version == '7':
    subprocess.call(["systemctl", "start", "dd-process-agent"])
except:
    logger.error("could not start the dd-process-agent")
