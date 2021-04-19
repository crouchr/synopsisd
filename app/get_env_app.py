# environment specific to this app
import os


def get_mins_between_updates():
    """
    Set time between consecutive updates
    """

    if 'MINS_BETWEEN_UPDATES' in os.environ:
        mins_between_updates = int(os.environ['MINS_BETWEEN_UPDATES'])
    else:
        mins_between_updates = 10    # was 15

    return mins_between_updates


# Solar multiplier = theoretical / measured on a cloudless day at noon
def get_solar_multiplier():
    if 'SOLAR_MULTIPLIER' in os.environ:
        solar_multiplier = os.environ['SOLAR_MULTIPLIER']
    else:
        solar_multiplier = 1.7       # value in Ermin Street

    return solar_multiplier


# elevation in metres
def get_site_elevation():
    if 'SITE_ELEVATION' in os.environ:
        site_elevation = os.environ['SITE_ELEVATION']
    else:
        site_elevation = 50
    return site_elevation