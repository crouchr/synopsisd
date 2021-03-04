import cumulus_comms
from pprint import pprint


# FIXME : This function is common with webcamd - consolidate
def get_key_weather_variables(cumulus_endpoint):
    """
    Get some critical weather variables by querying the CumulusMX REST API
    """

    status_code, response_dict = cumulus_comms.call_rest_api(cumulus_endpoint, None)

    # Aercus to CumulusMX serial connection down - all data now invalid
    if status_code == 200 and response_dict['DataStopped'] :
        return None

    if status_code == 200:
        return response_dict
    else:
        return None
