import call_rest_api
from pprint import pprint

# This function is common with webcamd - consolidate
def get_key_weather_variables(cumulus_endpoint):
    """
    Get some critical weather variables by querying the CumulusMX REST API
    """

    status_code, response_dict = call_rest_api.call_rest_api(cumulus_endpoint, None)

    # Aercus to CumulusMX serial connection down - all data now invalid
    if status_code == 200 and response_dict['DataStopped'] :
        return None

    if status_code == 200:
        return response_dict
    else:
        return None

