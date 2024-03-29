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
import jena_data
import mean_sea_level_pressure

# artifacts (metrestapi)
import cumulus_comms

# artifacts (metminifuncs)
import sync_start_time

# imports
import get_cumulus_weather_info
import get_env
import get_env_app
import definitions
import sync_start_time

# Add a bunch of reliability code to this before deploying

# FIXME : UTC
# The WMO synopsis should only use sensor data that does not need Internet - i.e. totally independent AWS
def update_synopsis_file(timestamp, synopsis_file_fp, this_uuid, temp_c, wet_bulb_c, dew_point_c, feels_like_c,
                         humidity,
                         pressure,
                         rain_rate, last_rain_tip, rain_last_24h,
                         dominant_wind_direction, wind_knots_2m, recent_max_gust,
                         solar, solar_rad_corrected, altitude_deg, azimuth_deg, uv_index, okta, okta_text,
                         synopsis_code, synopsis_text, forecast,
                         version):
    # Post an invalid WMO code - a high value will also be highlighted on the Grafana output
    # There is no WMO code for 'data invalid' so use a 'reserved' one
    if temp_c == -999:
        synopsis_text = "ERR"
        synopsis_str = 'WMO_4680_ERR'
    else:
        synopsis_str = 'WMO_4680_%02d' % synopsis_code

    if synopsis_text == 'No significant weather observed' or synopsis_text == '-None-':
        synopsis_text = '---'

    rec_tsv = timestamp + '\t' + \
        synopsis_str + '\t' + \
        temp_c.__str__() + '\t' + \
        wet_bulb_c.__str__() + '\t' + \
        dew_point_c.__str__() + '\t' + \
        feels_like_c.__str__() + '\t' + \
        humidity.__str__() + '\t' + \
        pressure.__str__() + '\t' + \
        solar.__str__() + '\t' + \
        solar_rad_corrected.__str__() + '\t' + \
        altitude_deg.__str__() + '\t' + \
        azimuth_deg.__str__() + '\t' + \
        uv_index.__str__() + '\t' + \
        dominant_wind_direction.__str__() + '\t' + \
        wind_knots_2m.__str__() + '\t' + \
        recent_max_gust.__str__() + '\t' + \
        okta.__str__() + '\t' + \
        okta_text.__str__() + '\t' + \
        rain_rate.__str__() + '\t' + \
        last_rain_tip.__str__() + '\t' + \
        rain_last_24h.__str__() + '\t' + \
        '"' + synopsis_text + '"' + '\t' + \
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
        solar_multiplier = get_env_app.get_solar_multiplier()
        site_elevation_m = get_env_app.get_site_elevation()

        print(my_app_name + ' started, version=' + version)
        print('stage=' + stage)
        if stage == 'DEV':
            verbose = True
        print('verbose=' + verbose.__str__())
        print('cumulusmx endpoint=' + cumulusmx_endpoint)
        print('solar_multiplier=' + solar_multiplier.__str__())
        print('site_elevation_m=' + site_elevation_m.__str__())

        synopsis_filename = definitions.SYNOPSIS_ROOT + 'synopsis.tsv'
        print('synopsis_filename=' + synopsis_filename)
        synopsis_file_fp = open(synopsis_filename, 'a')        # file does not need to exist / be touched before this script runs

        print('entering main loop...')
        while True:
            print('waiting to sync main loop...')
            sync_start_time.wait_until_minute_flip(10) # comment this out when testing
            start_secs = time.time()
            this_uuid = str(uuid.uuid4())                               # unique uuid per cycle
            record_timestamp = jena_data.get_jena_timestamp()           # UTC
            cumulus_weather_info = get_cumulus_weather_info.get_key_weather_variables(cumulusmx_endpoint)     # REST API call
            # cumulus_weather_info = None
            if cumulus_weather_info is None:    # can't talk to CumulusMX
                print('Error: CumulusMX did not return valid data')
                cumulus_comms.wait_until_cumulus_data_ok(cumulusmx_endpoint)  # loop until CumulusMX data is OK
                continue

            temp_c = float(cumulus_weather_info['OutdoorTemp'])

            # Burt says to record pressure adjusted to MSL (Mean Sea Level)
            pressure = float(cumulus_weather_info['Pressure'])
            pressure = round(pressure + mean_sea_level_pressure.msl_k_factor(site_elevation_m, temp_c), 1)

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
            synopsis_code, synopsis_text = synopsis.get_synopsis(temp_c, wet_bulb_c, dew_point_c, rain_rate, wind_knots_2m, solar, humidity)
            if 'fog' in synopsis_text.lower():
                is_fog = True
            else:
                is_fog = False

            # solar geometry
            altitude_deg = solar_rad_expected.calc_altitude(definitions.ermin_lat, definitions.ermin_lon)
            azimuth_deg = solar_rad_expected.calc_azimuth(definitions.ermin_lat, definitions.ermin_lon)
            solar_radiation_theoretical = solar_rad_expected.get_solar_radiation_theoretical(altitude_deg)
            solar_rad_corrected = int(solar * solar_multiplier)

            # derived cloud coverage estimate
            cloud_coverage_percent = solar_rad_expected.calc_cloud_coverage(definitions.ermin_lat, definitions.ermin_lon, solar_rad_corrected, solar_radiation_theoretical)
            okta = okta_funcs.coverage_to_okta(cloud_coverage_percent, is_fog)
            okta_text = okta_funcs.convert_okta_to_cloud_cover(okta)[0]

            update_synopsis_file(record_timestamp, synopsis_file_fp, this_uuid,
                                 temp_c, wet_bulb_c, dew_point_c, feels_like_c, humidity, pressure,
                                 rain_rate, last_rain_tip, rain_last_24h,
                                 dominant_wind_direction, wind_knots_2m, recent_max_gust,
                                 solar, solar_rad_corrected, altitude_deg, azimuth_deg,
                                 uv_index,
                                 okta, okta_text,
                                 synopsis_code, synopsis_text,
                                 forecast,
                                 version
                                 )
            stop_secs = time.time()
            # mins_between_updates = 1
            sleep_secs = (mins_between_updates * 60) - (stop_secs - start_secs) - 10
            time.sleep(sleep_secs)

    except Exception as e:
        print('Error : ' + e.__str__())
        traceback.print_exc()


if __name__ == '__main__':
    main()
