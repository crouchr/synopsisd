# Infinite loop for updating a file with Curretn Weather (synopsis) based purely only on AWS data
# This code was originally copied from webcamd

import time
import uuid
import traceback
from pprint import pprint

# artifacts (metfuncs)
import wet_bulb
import synopsis
import okta_funcs
import solar_rad_expected

# artifacts (metrestapi)
import cumulus_comms

import get_cumulus_weather_info
import get_env
import get_env_app
import definitions


# Add a bunch of reliability code to this before deploying

# FIXME : UTC
# The WMO synopsis should only use sensor data that does not need Internet - i.e. totally independent AWS
def update_synopsis_file(synopsis_file_fp, this_uuid, temp_c, wet_bulb_c, dew_point_c, feels_like_c, humidity, pressure, rain_rate, last_rain_tip, rain_last_24h, dominant_wind_direction, wind_knots_2m, recent_max_gust, solar, uv_index, okta, okta_text, synopsis_code, synopsis_text, forecast, version):
    # Post an invalid WMO code - a high value will also be highlighted on the Grafana output
    # There is no WMO code for 'data invalid' so use a 'reserved' one
    if temp_c == -999:
        synopsis_text = "ERR"
        synopsis_str = 'WMO_4680_ERR'
    else:
        synopsis_str = 'WMO_4680_%02d' % synopsis_code

    if synopsis_text == 'No significant weather observed' or synopsis_text == '-None-':
        synopsis_text = '---'

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
        okta.__str__() + '\t' + \
        okta_text.__str__() + '\t' + \
        rain_rate.__str__() + '\t' + \
        last_rain_tip.__str__() + '\t' + \
        rain_last_24h.__str__() + '\t' + \
        '"' + forecast.__str__() + '"' + '\t' + \
        version.__str__()

    rec_tsv_no_tabs = rec_tsv.replace('\t', ' ')    # nicer output in PaperTrail
    print(rec_tsv_no_tabs)

    synopsis_file_fp.write(rec_tsv + '\n')
    synopsis_file_fp.flush()


def main():
    try:
        my_app_name = 'synopsisd'
        version = get_env.get_version()
        verbose = get_env.get_verbose()
        stage = get_env.get_stage()
        # cumulusmx_endpoint = '192.168.1.99' # for testing REST API failure handling
        cumulusmx_endpoint = get_env.get_cumulusmx_endpoint()

        mins_between_updates = get_env_app.get_mins_between_updates()
        lat = 51.4151  # Stockcross
        lon = -1.3776  # Stockcross

        print(my_app_name + ' started, version=' + version)
        print('stage=' + stage)
        if stage == 'DEV':
            verbose = True
        print('verbose=' + verbose.__str__())
        print('cumulusmx endpoint=' + cumulusmx_endpoint)

        synopsis_filename = definitions.SYNOPSIS_ROOT + 'synopsis.tsv'
        print('synopsis_filename=' + synopsis_filename)
        synopsis_file_fp = open(synopsis_filename, 'a')        # file does not need to exist / be touched before this script runs

        print('entering main loop...')
        while True:
            this_uuid = str(uuid.uuid4())          # unique uuid per cycle

            cumulus_weather_info = get_cumulus_weather_info.get_key_weather_variables(cumulusmx_endpoint)     # REST API call
            # cumulus_weather_info = None
            if cumulus_weather_info is None:    # can't talk to CumulusMX
                print('Error: CumulusMX did not return valid data')
                cumulus_comms.wait_until_cumulus_data_ok(cumulusmx_endpoint)  # loop until CumulusMX data is OK
                continue

            pressure = float(cumulus_weather_info['Pressure'])
            temp_c = float(cumulus_weather_info['OutdoorTemp'])
            dew_point_c = float(cumulus_weather_info['OutdoorDewpoint'])
            humidity = float(cumulus_weather_info['OutdoorHum'])
            rain_rate = float(cumulus_weather_info['RainRate'])
            wind_knots_2m = float(cumulus_weather_info['WindAverage'])  # my vane is approx 4m above ground not 2m
            forecast = cumulus_weather_info['Forecast']
            solar = int(cumulus_weather_info['SolarRad'])               # contributes to is_fog()
            dominant_wind_direction = cumulus_weather_info['DominantWindDirection']
            recent_max_gust = float(cumulus_weather_info['Recentmaxgust'])
            uv_index = float(cumulus_weather_info['UVindex'])
            feels_like_c = float(cumulus_weather_info['FeelsLike'])
            last_rain_tip = cumulus_weather_info['LastRainTipISO']      # feed into FOG ?
            rain_last_24h = cumulus_weather_info['RainLast24Hour']      # feed into FOG ?
            version = cumulus_weather_info['Version']                   # CumulusMX version

            # derived value
            wet_bulb_c = wet_bulb.get_wet_bulb(temp_c, pressure, dew_point_c)

            # determine the WMO synopsis
            synopsis_code, synopsis_text = synopsis.get_synopsis(temp_c, wet_bulb_c, dew_point_c, rain_rate, wind_knots_2m, solar)
            if 'fog' in synopsis_text.lower():
                is_fog = True
            else:
                is_fog = False

            # solar geometry
            altitude_deg = solar_rad_expected.calc_altitude(lat, lon)
            solar_radiation_theoretical = solar_rad_expected.get_solar_radiation_theoretical(altitude_deg)

            # derived cloud coverage estimate
            cloud_coverage_percent = solar_rad_expected.calc_cloud_coverage(lat, lon, solar, solar_radiation_theoretical)
            okta = okta_funcs.coverage_to_okta(cloud_coverage_percent, is_fog)
            okta_text = okta_funcs.convert_okta_to_cloud_cover(okta)[0]

            update_synopsis_file(synopsis_file_fp, this_uuid, temp_c, wet_bulb_c, dew_point_c, feels_like_c, humidity, pressure, rain_rate, last_rain_tip, rain_last_24h, dominant_wind_direction, wind_knots_2m, recent_max_gust, solar, uv_index, okta, okta_text, synopsis_code, synopsis_text, forecast, version)

            sleep_secs = mins_between_updates * 60
            time.sleep(sleep_secs)

    except Exception as e:
        print('Error : ' + e.__str__())
        traceback.print_exc()


if __name__ == '__main__':
    main()

