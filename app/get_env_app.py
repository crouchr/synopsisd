# environment specific to this app
import os


def get_video_length():
    """
    Set webcam video duration in Docker Compose ENV
    """
    if 'VIDEO_SECS' in os.environ:
        video_length_secs = int(os.environ['VIDEO_SECS'])
    else:
        video_length_secs = 20
        return video_length_secs


def get_video_preamble():
    """
    Set webcam video preamble duration in Docker Compose ENV
    """

    if 'PREAMBLE_SECS' in os.environ:
        preamble_secs = int(os.environ['PREAMBLE_SECS'])
    else:
        preamble_secs = 5

    return preamble_secs


def get_min_solar():
    """
    Set minimum value of solar level to take video in (watts/metre-squared)
    """

    if 'MIN_SOLAR' in os.environ:
        min_solar = os.environ['MIN_SOLAR']     # a float
    else:
        min_solar = 0.5

    return min_solar


def get_max_solar():
    """
    Set maximum value of solar level to take video in (watts/metre-squared)
    i.e. get reflections from window when curtains are closed
    """

    if 'MAX_SOLAR' in os.environ:
        max_solar = os.environ['MAX_SOLAR']     # a float
    else:
        max_solar = 130.0

    return max_solar


def get_mins_between_updates():
    """
    Set time between consecutive updates
    """

    if 'MINS_BETWEEN_UPDATES' in os.environ:
        mins_between_updates = int(os.environ['MINS_BETWEEN_UPDATES'])
    else:
        mins_between_updates = 10    # was 15

    return mins_between_updates

