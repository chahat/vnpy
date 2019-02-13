import logging
import time
from datetime import datetime, timedelta

import requests

logger = logging.getLogger()

API_URL = 'https://api.gdax.com'

PRODUCTS = {
    'BTC-USD': '2015-01-08'
}


def configure_logging(loglevel):
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(loglevel)


def daterange(start, end, step):
    curr = start
    while curr < end:
        yield curr, curr+step
        curr += step


def get(url, params):
    # todo: handle non-http errors: timeout, ConnectionError, etc.
    tries = 3
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=(10, 10))
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Only 4XX code we want to re-try is 429 (api rate limit)
            # Other client error codes such as "400 Bad Request" or
            # "403 Forbidden" will always fail no matter how often we try
            if e.response.status_code in (429, 500) and (i < tries - 1):
                logger.warning(e)
                logger.info('Re-trying')
                # api rate limit is 3 requests per second
                # we do 1 request per second to be safe
                time.sleep(1)
                continue
            else:
                raise
        break
    return r.json()


def get_candles(product, start_date, end_date=datetime.now()):
    # "your response may contain as many as 300 candles"
    # we need one candle per minute (granularity=60)
    d = timedelta(minutes=300)

    # the most recent values are going to change, to avoid saving them
    # to the database, we will exclude them and fetch them the next run
    end_date = end_date - d

    if end_date < start_date:
        logger.debug('start date {%s} is after end date {%s}'%(start_date, end_date))
        return

    previous_start_date = start_date.date()
    for start, end in daterange(start_date, end_date, d):
        logger.debug('{%s} | {%s} -> {%s} | {%s} -> {%s}'%(product, start, end, start_date, end_date))

        # logging should only show day-by-day progress
        if start.date() != previous_start_date:
            logger.info('{%s} | importing {%s}'%(product, start.date()))

        params = {'start': start.isoformat(),
                  'end': end.isoformat(),
                  'granularity': 60}
        try:
            data = get('%s/products/%s/candles'%(API_URL, product), params=params)
        except requests.exceptions.HTTPError as e:
            # if re-trying doesnt work, we skip to next product
            # the next run can resume from latest value
            logger.error('Unable to fetch candles (max-retries exceeded)')
            logger.error(e)
            return

        previous_start_date = start.date()
        yield data


def get_start_date(product):
    start_date = datetime.strptime(PRODUCTS[product], '%Y-%m-%d')
    return start_date


def main():
    for i, product in enumerate(PRODUCTS, 1):
        start_date = get_start_date(product)
        for candles in get_candles(product, start_date):
            print(candles)
            time.sleep(0.5)


if __name__ == '__main__':
    main()