import requests
import os

from json import dump
from datetime import date

GENERATED_DATA_PATH = 'generated_data'
TODAY  = str(date.today())
MIN_SIZE = 5192 #Any responses under this size (in bytes) will be considered an error message

# def generic_request(request):
#     return requests.get(request, headers=headers)

def request_ticker_historical(ticker, token):
    """
    Get historical data for ticker
    Output as csv

    return: 0 success 1 fail
    """

    headers = {
    'Content-Type': 'application/json',
    'Authorization' : 'Token ' + token
    }

    current_path = os.getcwd()
    if not os.path.exists(f"{current_path}/{GENERATED_DATA_PATH}/{TODAY}"):
        os.makedirs(f"{current_path}/{GENERATED_DATA_PATH}/{TODAY}")

    response = requests.get(f"https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate=1800-1-1&endDate={TODAY}&format=csv", headers=headers)
    if response.text.__sizeof__() < MIN_SIZE:
        print(f"{response.text}")
        return 1
    try:
        with open(f"{GENERATED_DATA_PATH}/{TODAY}/{ticker}.csv", 'w') as f:
            bytes_written = f.write(response.text)
            print(f"Completed {ticker}: wrote {bytes_written}B")
            return 0
    except:
        print(f"{response.text}")
        return 1

def create_tickers_txt():

    current_path = os.getcwd()
    if not os.path.exists(f"{current_path}/{GENERATED_DATA_PATH}"):
        os.makedirs(f"{current_path}/{GENERATED_DATA_PATH}")


    list = []
    with open('supported_tickers.csv', 'r') as tickers:

        for line in tickers:

            split_line = line.split(',')
            ticker = split_line[0]
            exchange_temp = split_line[1]
            list.append(f"{exchange_temp}:{ticker}")

    with open(f"{GENERATED_DATA_PATH }/tickers.txt", 'w') as txt:
        for t in list:
            txt.write(t + '\n')


def clean_completed():
    ghosts = []
    try:
        path = os.path.join(os.getcwd(), GENERATED_DATA_PATH, TODAY)
        files = os.listdir(path)
        for file in files:
            parts = file.split('.')
            if len(parts) == 2:
                if parts[1] == 'csv':
                    path = f"{os.getcwd()}/{GENERATED_DATA_PATH}/{TODAY}/{file}"
                    if os.path.getsize(path) < MIN_SIZE:
                        os.remove(path)
                        ghosts.append(parts[0])
        print(f"Ghosts: {ghosts}")

        path = os.path.join(os.getcwd(), GENERATED_DATA_PATH, TODAY, "completed.txt")
        with open(path, 'r') as f:
            new_lines = []
            old_lines = f.readlines()
            for line in old_lines:
                if (line.strip('\n') not in ghosts) and (line.strip('\n') not in new_lines):
                    new_lines.append(line.strip('\n'))

        if os.path.exists(path):
            os.remove(path)
        else:
            print("The file does not exist")
        with open(path, 'w') as f1:
            for line in new_lines:
                f1.write(line + '\n')
                print(line)

    except Exception as e:
        print(e)

def request_daily_data(list_txt, limit):

    completed_tickers = []
    total_tickers = 0

    try:
        with open(f"{GENERATED_DATA_PATH}/{TODAY}/completed.txt", 'r') as f1:
            for line in f1.readlines():
                completed_tickers.append(line.strip('\n'))
    except:
        print("No data found for {TODAY}")
    
    if len(completed_tickers) != 0:
        print(f"{TODAY} data already found for {len(completed_tickers)} tickers")

    with open(list_txt, 'r') as f2:

        lines = f2.readlines()
        total_tickers = len(lines)

        j = 0
        for i in range(len(lines)):
            if j >= limit:
                break

            exit_code = 0
            split_line = lines[i].split(':')

            if len(split_line) >= 2:
                ticker = lines[i].split(':')[1][:-1]
                #exchange = lines[i].split(':')[0]
            else:
                ticker = split_line[0][:-1]

            if ticker not in completed_tickers:
                exit_code = request_ticker_historical(ticker)
                if exit_code > 0:
                    break
                else:
                    completed_tickers.append(ticker)
                    j += 1
            else:
                print(f"{TODAY} data already found for {ticker}, skipping...")

        

    print(f"{len(completed_tickers)}/{total_tickers} tickers completed")

    with open(f"{GENERATED_DATA_PATH}/{TODAY}/completed.txt", 'a') as f3:
        for ticker in completed_tickers:
            f3.write(f"{ticker}\n")

        #Remove any entries that shouldn't be there (corresponding csv is empty)

    


# list_txt = "priority_tickers.txt"
# limit = 50
# create_tickers_txt()
# clean_completed()
# request_daily_data(list_txt, limit)
# today = str(date.today())
# response = generic_request("https://api.tiingo.com/tiingo/daily/NVDA/prices?startDate=1800-1-1&endDate="+ today +"&format=csv")
# with open(GENERATED_DATA_PATH + '/test.csv', 'w') as f:
#     f.write(response.text)
