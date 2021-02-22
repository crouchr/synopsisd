import call_rest_api
from pprint import pprint


def get_key_weather_variables(cumulus_endpoint):
    """
    Get some critical weather variables by querying the CumulusMX REST API
    """

    status_code, response_dict = call_rest_api.call_rest_api(cumulus_endpoint, None)
    # print('status_code=' + status_code.__str__())
    #pprint(response_dict)

    if status_code == 200:
        return response_dict
    else:
        return None

