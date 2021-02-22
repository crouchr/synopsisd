# common environment non-specific to this app
# This file can be used in other metminiwx projects

import os


def get_version():
    if 'VERSION' in os.environ:
        version = os.environ['VERSION']
    else:
        version = 'IDE-1.0.0'       # i.e. running in PyCharm

    return version


def get_verbose():
    if 'VERBOSE' in os.environ:
        verbose = os.environ['VERBOSE']
        if verbose == 'True':
            verbose = True
        else:
            verbose = False
    else:
        verbose = False

    return verbose


def get_stage():
    if 'STAGE' in os.environ:
        stage = os.environ['STAGE']
    else:
        stage = 'DEV'               # i.e. running in PyCharm

    return stage


def get_webcam_service_endpoint():
    if 'STAGE' in os.environ and os.environ['STAGE'] == 'PRD':
        webcam_service_endpoint_base = 'http://webcam-service:9504'
    else:
        webcam_service_endpoint_base = 'http://192.168.1.180:9504'

    return webcam_service_endpoint_base


def get_twitter_service_endpoint():
    if 'STAGE' in os.environ and os.environ['STAGE'] == 'PRD':
        twitter_service_endpoint_base = 'http://webcam-service:9506'
    else:
        twitter_service_endpoint_base = 'http://192.168.1.180:9506'

    return twitter_service_endpoint_base


def get_cumulusmx_endpoint():
    if 'STAGE' in os.environ and os.environ['STAGE'] == 'PRD':
        cumulusmx_endpoint = 'http://cumulusmx:8998/api/data/currentdata'
    else:
        cumulusmx_endpoint = 'http://192.168.1.180:8998/api/data/currentdata'

    return cumulusmx_endpoint

# Not needed but trying to have a common file
# def get_telegraf_endpoint():
#     if 'TELEGRAF_ENDPOINT' in os.environ:
#         telegraf_endpoint = os.environ['TELEGRAF_ENDPOINT']
#     else:
#         telegraf_endpoint = '192.168.1.180'

    return telegraf_endpoint