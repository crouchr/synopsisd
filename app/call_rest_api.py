# This needs to be added to a library
import requests
import json
from pprint import pprint


# FIXME : add retries, authentication etc in the future
# returning 200 even if return data is not good - this should be 500 ?
def call_rest_api(endpoint, query):
    """
    Call REST API endpoint

    :param endpoint:e.g. 'http://127.0.0.1:9500/wind_deg_to_wind_rose'
    :param query: e.g. query = {'wind_deg': wind_deg}
    :return:
    """
    try:
        # print('call_rest_api() : endpoint=' + endpoint)
        if query is not None:
            pprint(query.__str__())
        response = requests.get(endpoint, params=query)
        if response.status_code != 200:
            return 500, None

        response_dict = json.loads(response.content.decode('utf-8'))

        return response.status_code, response_dict

    except Exception as e:
        print('call_rest_api() : Error=' + e.__str__())
        return 500, None

