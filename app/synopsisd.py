# Infinite loop for updating a file with Curretn Weather (synopsis) based purely only on AWS data
# This code was originally copied from webcamd

import time
import uuid
import traceback
from pprint import pprint

# artifacts
import wet_bulb
import synopsis

import call_rest_api
# import definitions
import get_cumulus_weather_info
import get_env
import get_env_app
import definitions

# Add a bunch of reliability code to this before deploying


# def send_tweet(tweet_text, uuid):
#     """
#     Send a Tweet - i.e. not enough light etc, so just send the met info
#     """
#     query = {}                                  # API call to twitter-service
#     query['app_name'] = 'webcamd'
#     query['uuid'] = uuid
#     query['tweet_text'] = tweet_text
#     query['hashtag_arg'] = 'metminiwx'          # do not supply the #
#     query['lat'] = 51.4151                      # FIXME - put in definitions.py Stockcross
#     query['lon'] = -1.3776                      # Stockcross
#
#     status_code, response_dict = call_rest_api.call_rest_api(get_env.get_twitter_service_endpoint() + '/send_text', query)
#
#     if response_dict['status'] == 'OK' :
#         tweet_len = response_dict['tweet_len'].__str__()
#         print('Tweet sent OK, tweet_len=' + tweet_len + ', uuid=' + uuid.__str__())
#     else:
#         print(response_dict['status'])


# def send_tweet_with_video(tweet_text, filename, uuid):
#     """
#     Send a Tweet with a video file
#     """
#     query = {}                                  # API call to twitter-service
#     query['app_name'] = 'webcamd'
#     query['uuid'] = uuid
#     query['tweet_text'] = tweet_text
#     query['hashtag_arg'] = 'metminiwx'          # do not supply the #
#     query['lat'] = 51.4151                      # Stockcross
#     query['lon'] = -1.3776                      # Stockcross
#     query['video_pathname'] = filename
#
#     status_code, response_dict = call_rest_api.call_rest_api(get_env.get_twitter_service_endpoint() + '/send_video', query)
#
#     # print('status_code=' + status_code.__str__())
#     # pprint(response_dict)
#     # if response_dict['status'] == 'OK' and response_dict['tweet_sent'] == True:
#     if response_dict['status'] == 'OK' :
#         tweet_len = response_dict['tweet_len'].__str__()
#         print('Tweet sent OK, tweet_len=' + tweet_len + ', uuid=' + uuid.__str__())
#     else:
#         print(response_dict['status'])

# FIXME : leading zero
# FIXME : UTC
# The WMO synopsis should only use sensor data that does not need Internet - i.e. totally independent AWS
def update_synopsis_file(synopsis_file_fp, this_uuid, temp_c, wet_bulb_c, dew_point_c, feels_like_c, humidity, pressure, rain_rate, dominant_wind_direction, wind_knots_2m, recent_max_gust, solar, uv_index, synopsis_code, synopsis_text, forecast):
    # Post an invalid WMO code - a high value will also be highlighted on the Grafana output
    # There is no WMO code for 'data invalid' so use a 'reserved' one
    if temp_c == -999:
        synopsis_text = "Unable to read data from station - all data is invalid"
        synopsis_str = 'WMO_4680_ERR'
    else:
        synopsis_str = 'WMO_4680_%02d' % synopsis_code

    rec_tsv = time.ctime() + '\t' + \
        synopsis_str + '\t' + \
        '"' + synopsis_text + '"' + '\t' + \
        temp_c.__str__() + '\t' + \
        wet_bulb_c.__str__() + '\t' + \
        dew_point_c.__str__() + '\t' + \
        feels_like_c.__str__() + '\t' + \
        humidity.__str__() + '\t' + \
        pressure.__str__() + '\t' + \
        solar.__str__() + '\t' + \
        uv_index.__str__() + '\t' + \
        dominant_wind_direction.__str__() + '\t' + \
        wind_knots_2m.__str__() + '\t' + \
        recent_max_gust.__str__() + '\t' + \
        rain_rate.__str__() + '\t' + \
        '"' + forecast.__str__() + '"'

    print(rec_tsv)
    synopsis_file_fp.write(rec_tsv + '\n')
    synopsis_file_fp.flush()


def main():
    try:
        my_app_name = 'synopsisd'
        version = get_env.get_version()
        verbose = get_env.get_verbose()
        stage = get_env.get_stage()
        cumulusmx_endpoint = get_env.get_cumulusmx_endpoint()
        # cumulusmx_endpoint = '192.168.1.99' # for testing REST API failure handling

        # webcam_service_endpoint = get_env.get_webcam_service_endpoint()
        # video_length_secs = get_env_app.get_video_length()
        # preamble_secs = get_env_app.get_video_preamble()
        # min_solar = get_env_app.get_min_solar()
        # max_solar = get_env_app.get_max_solar()
        mins_between_updates = get_env_app.get_mins_between_updates()

        # webcam_query = {}                       # API call to webcam-service
        # webcam_query['app_name'] = my_app_name
        # webcam_query['video_length_secs'] = video_length_secs
        # webcam_query['preamble_secs'] = preamble_secs

        print(my_app_name + ' started, version=' + version)
        print('stage=' + stage)
        if stage == 'DEV':
            verbose = True
        print('verbose=' + verbose.__str__())
        print('cumulusmx endpoint=' + cumulusmx_endpoint)

        # print('webcam-service endpoint=' + webcam_service_endpoint)
        # print('min_solar=' + min_solar.__str__())
        # print('max_solar=' + max_solar.__str__())
        # print('preamble_secs=' + preamble_secs.__str__())
        # print('video_length_secs=' + video_length_secs.__str__())

        synopsis_filename = definitions.SYNOPSIS_ROOT + 'synopsis.tsv'
        print('synopsis_filename=' + synopsis_filename)
        synopsis_file_fp = open(synopsis_filename, 'a')        # file does not need to exist / be touched before this script runs

        print('entering main loop...')
        while True:
            this_uuid = str(uuid.uuid4())          # unique uuid per cycle

            cumulus_weather_info = get_cumulus_weather_info.get_key_weather_variables(cumulusmx_endpoint)     # REST API call
            if cumulus_weather_info is None:    # can't talk to Cumulux
                print(time.ctime() + ' Error : Aercus to CumulusMX REST API failure')
                update_synopsis_file(synopsis_file_fp, this_uuid, -999, -999, -999, -999, -999, -999, -999, -999, None)
                time.sleep(120)
                continue

            pressure = float(cumulus_weather_info['Pressure'])
            temp_c = float(cumulus_weather_info['OutdoorTemp'])
            dew_point_c = float(cumulus_weather_info['OutdoorDewpoint'])
            humidity = float(cumulus_weather_info['OutdoorHum'])
            rain_rate = float(cumulus_weather_info['RainRate'])
            wind_knots_2m = float(cumulus_weather_info['WindAverage'])  # my vane is approx 4m above ground not 2m
            forecast = cumulus_weather_info['Forecast']
            solar = int(cumulus_weather_info['SolarRad'])               # contribute to is_fog() ?
            dominant_wind_direction = cumulus_weather_info['DominantWindDirection']
            recent_max_gust = float(cumulus_weather_info['Recentmaxgust'])
            uv_index = float(cumulus_weather_info['UVindex'])
            feels_like_c = float(cumulus_weather_info['FeelsLike'])

            # derived value
            wet_bulb_c = wet_bulb.get_wet_bulb(temp_c, pressure, dew_point_c)

            # determine the WMO synopsis
            # synopsis_code, synopsis_text = synopsis.get_synopsis(temp_c, wet_bulb_c, dew_point_c, rain_rate, wind_knots_2m, solar)
            synopsis_code, synopsis_text = synopsis.get_synopsis(temp_c, wet_bulb_c, dew_point_c, rain_rate, wind_knots_2m)
            # solar not supported yrt in metfuncs

            # Aercus to CumulusMX USB channel not working
            if cumulus_weather_info['DataStopped'] == True:
                print(time.ctime() + ' Error : Aercus to CumulusMX USB connection failure')
                update_synopsis_file(synopsis_file_fp, this_uuid, -999, -999, -999, -999, -999, -999, -999, -999, -999, -999,-999, -999, -999)
            else:
                update_synopsis_file(synopsis_file_fp, this_uuid, temp_c, wet_bulb_c, dew_point_c, feels_like_c, humidity, pressure, rain_rate, dominant_wind_direction, wind_knots_2m, recent_max_gust, solar, uv_index, synopsis_code, synopsis_text, forecast)

            sleep_secs = mins_between_updates * 60
            time.sleep(sleep_secs)

    except Exception as e:
        traceback.print_exc()


if __name__ == '__main__':
    main()

