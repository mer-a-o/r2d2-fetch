#!/bin/bash

source /discover/nobackup/projects/gmao/advda/swell/jedi_modules/spackstack_1.9_intel_bundle

module use -a /discover/nobackup/projects/gmao/advda/JediOpt/modulefiles/core
module load r2d2-client/112025

# cfdev_server
# put your username and api_key
export R2D2_USER=""
export R2D2_API_KEY=""
export R2D2_HOST="discover"
export R2D2_COMPILER="intel"
export R2D2_SERVER_HOST="http://13.217.72.149"
export R2D2_SERVER_PORT="8080"
