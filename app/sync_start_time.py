# make this a common function
import time


def wait_until_minute_flip():
    """
    Wait until seconds it 00
    :return:
    """
    while True:
        a = time.ctime()
        parts = a.split(' ')
        time_str = parts[3]
        secs = time_str.split(':')[2]
        time.sleep(0.2)
        if secs == '00':
            return


if __name__ == '__main__':
    wait_until_minute_flip()
