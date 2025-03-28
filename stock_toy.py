import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import requests
import os
import pandas as pd
import numpy as np
import math
from datetime import datetime
from datetime import date
from pyautogui import size
import random


SCREEN_X = size()[0]
SCREEN_Y = size()[1]

GENERATED_DATA_PATH = "generated_data"
TICKERS_LIST_FOLDER = "tickers"
MIN_SIZE = 5192 #Any responses under this size (in bytes) will be considered an error message

WIDTH = int(SCREEN_X * 0.75)
HEIGHT = int(SCREEN_Y * 0.75)

GREEN = [0,200,0,255]
YELLOW = [200,200,0,255]
RED = [200,0,0,255]

TODAY  = str(date.today())

init = "default.ini"
ticker_data_age = {}
tickers_toggled = set()
tokens = []

loading = False

ticker_data = {}
ticker_data_simulated = {} #nested dict, one dict for each sim

tickers_file = ""

def load_init(sender, app_data):
    global init
    init = dpg.get_item_label(sender)
    dpg.stop_dearpygui()
    
def save_ini(sender, app_data, user_data):
    filename = dpg.get_value("save_ini_text")
    if filename[-4:] == ".ini":
        dpg.configure_item("save_ini_popup", show=False)
        dpg.save_init_file(filename)
        log_message(f"Saved configuration as {filename}")
    else:
        dpg.configure_item("invalid_filename_popup", show=True)


def get_ini_files():
    files = [f for f in os.listdir(os.getcwd()) if f[-4:] == ".ini"]
    return files

def get_api_files():
    token_folder_path = os.path.join(os.getcwd(), "api_tokens")
    files = [f for f in os.listdir(token_folder_path) if f[-4:] == ".txt"]
    return files

def create_layout_options_window():
    temp = dpg.add_window(pos=[WIDTH/2, HEIGHT/2])
    dpg.add_text("Load layout:", parent=temp)
    dpg.add_separator(parent=temp)
    ini_files = get_ini_files()
    for file in ini_files:
        dpg.add_button(parent=temp, label=file, callback=load_init)

def load_tokens():

    global tokens

    files = get_api_files()
    for file in files:
        with open(os.path.join(os.getcwd(), "api_tokens", file), 'r') as f:
            tokens_temp = [line.rstrip() for line in f]
            tokens.extend(tokens_temp)
    log_message(f"Found {len(tokens)} token(s)")

def create_tickers_menu(ticker_file):
    tickers_counted = 0
    if ticker_file != "":
        dpg.hide_item("disabled_request_tooltip")
        with open(os.path.join("tickers", ticker_file), "r") as f:
            lines = [line.rstrip() for line in f]
            if len(lines) >= 1:
                dpg.configure_item("request_data_button", enabled=True)
            else:
                dpg.configure_item("request_data_button", enabled=False)

        dpg.delete_item("ticker_checkboxes")
        dpg.add_group(parent="ticker_window", tag="ticker_checkboxes", enabled = False)
        dpg.bind_item_theme("ticker_checkboxes", disabled_theme)
        
        for ticker in lines:
            with dpg.group(parent="ticker_checkboxes", tag=ticker + "_group", horizontal=True):
                dpg.add_checkbox(parent=ticker + "_group", callback=toggle_tickers, user_data=ticker)
                dpg.add_text(ticker,parent=ticker + "_group", tag=ticker + "_text")
            #Update the tickers dict and by default set them all as no data
            ticker_data_age[ticker] = None
            tickers_counted += 1

        #dpg.add_checkbox(label=f,parent=ticker_window)
    log_message(f"Found {tickers_counted} tickers in {ticker_file}")
    check_all_tickers_status()


def simulate_price_change(tickers, sim_number, sim_iterations):

    method = "random"
    ticker_count = len(tickers)
    log_message(f"Starting price forecasting for {ticker_count} ticker(s)...")
    for ticker in tickers:
        log_message(f"Forecasting price for {ticker}...")
        #Remove previous plot from previous simulation run if exists
        try:
            remove_plot_simulated_all(ticker)
        except:
            pass

        global ticker_data
        global ticker_data_simulated
        ticker_data_simulated[ticker] = {} 

        sim_number = int(sim_number)
        sim_iterations = int(sim_iterations)

        for i in range(sim_number):
            
            try:
                simulated_ages = ticker_data_simulated[ticker][i][0]
                simulated_prices = ticker_data_simulated[ticker][i][1]
            except Exception as e:
                
                if i == 0:
                    ticker_data_simulated[ticker] = {} 
                ticker_data_simulated[ticker][i] = [[ticker_data[ticker][0][-1]], [ticker_data[ticker][1][-1]]]
                simulated_ages = ticker_data_simulated[ticker][i][0]
                simulated_prices = ticker_data_simulated[ticker][i][1]

            actual_ages = ticker_data[ticker][0]
            actual_prices = ticker_data[ticker][1]

            for j in range(sim_iterations):
                np_combined_ages = np.append(actual_ages[0:-1], simulated_ages)
                np_combined_prices = np.append(actual_prices[0:-1], simulated_prices)
                #Do calculations on the next price here
                var = 1.01


                next_price = np_combined_prices[-1] * random.uniform(1.0/var, var)
                #Finish calcuations on next price above
                next_age = np_combined_ages[-1] - 1
                
                simulated_ages.append(next_age)
                simulated_prices.append(next_price)

                plot_simulated(ticker, i)

    log_message(f"Finished price forecasting for {ticker_count} tickers")

def plot_simulated_all(ticker):
    global ticker_data_simulated

    #Plot simulated data if exists (might not because user may not have run simulation yet)
    try:
        for num in ticker_data_simulated[ticker]:
            plot_simulated(ticker, num)
    except:
        pass
def remove_plot_simulated_all(ticker):
    # for sim_number in ticker_data_simulated[ticker]:
    #     print(sim_number)
    #     dpg.delete_item(f"{ticker}_plot_simulated_{sim_number}")
    pass

def set_loading(bool):
    global loading
    loading = bool

    if loading:
        dpg.configure_item("ticker_checkboxes", enabled = False)
    else:
        dpg.configure_item("ticker_checkboxes", enabled = True)

def update_tickers_file(new_file_path):
    global tickers_file
    tickers_file = new_file_path
    log_message(f"Using ticker file {tickers_file}")

def plot_simulated(ticker, sim_number):
    
    ages = ticker_data_simulated[ticker][sim_number][0]
    prices = ticker_data_simulated[ticker][sim_number][1]

    try:
        dpg.configure_item(f"{ticker}_plot_simulated_{sim_number}", x=ages, y=prices)
    except:
        dpg.add_line_series(x=ages, y=prices, parent="plot_y_axis", tag=f"{ticker}_plot_simulated_{sim_number}")
    # dpg.fit_axis_data('plot_x_axis')
    # dpg.fit_axis_data('plot_y_axis')

def check_all_tickers_status():

    old = 0
    new = 0
    none = 0


    global ticker_data_age


    test = 0
    data_path = os.path.join(os.getcwd(), "generated_data")
    directories = os.listdir(data_path)
    for d in directories:
        dir_path = (os.path.join(data_path, d))
        if os.path.isdir(dir_path):

            #Get data age in days
            age = (datetime.today() - datetime.strptime(d, "%Y-%m-%d")).days

            files = os.listdir(dir_path)

            for f in files:
                if f[-4:] == ".csv":
                    ticker = f[:-4]
                    ticker_data_age[ticker] = age
                    test += 1
    
    checkboxes_group_children = (dpg.get_item_children("ticker_checkboxes"))
    ticker_ui_groups = checkboxes_group_children[1]

    for t in ticker_ui_groups:
        checkbox_text = dpg.get_item_children(t)[1][1]
        text_value = dpg.get_value(dpg.get_item_children(t)[1][1])


        #Colour the ticker name based on data recency
        #Data taken today = Green
        #Data but not today = Yellow
        #No data = Red
        if ticker_data_age[text_value] != None:

            if ticker_data_age[text_value] == 0:
                dpg.configure_item(checkbox_text, color=GREEN)
                new += 1
            else:
                dpg.configure_item(checkbox_text, color=YELLOW)
                old += 1
        else:
            dpg.configure_item(checkbox_text, color=RED)
            none += 1

    log_message(f"Found the following data:")
    log_message(f"Current: {new}")
    log_message(f"Old: {old}")
    log_message(f"None: {none}")

    csv_to_plottable_all()
    

def csv_to_plottable_all():

    global ticker_data
    loaded = 0

    log_message(f"Searching for generated data folders...")

    folders = [f for f in os.listdir(os.path.join(os.getcwd(), "generated_data")) if os.path.isdir(os.path.join(os.getcwd(), "generated_data", f))]

    if len(folders) > 0:
        log_message(f"Found generated data for {len(folders)} different days")
        log_message(f"Loading data from csv files...")
        set_loading(True)
        for key in ticker_data_age:
            for f in folders:
                folder_age = (datetime.today() - datetime.strptime(f, "%Y-%m-%d")).days
                if folder_age == ticker_data_age[key]:
                    df = pd.read_csv(os.path.join(os.getcwd(), "generated_data", f, f"{key}.csv"))
                    dates = df['date']
                    prices = pd.Series.to_list(df['close'])
                    split_factors = pd.Series.to_list(df['splitFactor'])
                    
                    ages = pd.Series.to_list(dates.apply(date_to_age))
                    prices = convert_split_factor(prices, split_factors)

                    plot_data = [ages, prices]
                    ticker_data.update({key : plot_data})
                    loaded += 1


        log_message(f"Finished loading data for {loaded} tickers")

    else:
        log_message("No generated data was found")

    set_loading(False)
    
    


def convert_split_factor(prices, split_factors):

    current_split = 1
    for i in reversed(range(len(prices))):
        prices[i] /= current_split
        current_split *= split_factors[i]
    return prices

def date_to_age(date):
    return (datetime.today() - datetime.strptime(date, "%Y-%m-%d")).days

def toggle_item(sender, app_data, user_data):
    if dpg.get_item_configuration(user_data)["enabled"]:
        dpg.configure_item(user_data, enabled=False)
    else:
        dpg.configure_item(user_data,enabled=True)

def toggle_tickers(sender, app_data, user_data):
    global tickers_toggled
    ticker = user_data
    if dpg.get_value(sender): #Checkbox ticked
        tickers_toggled.add(ticker)
        add_to_plot(ticker)
    else:
        tickers_toggled.remove(ticker)
        remove_from_plot(ticker)

def add_to_plot(ticker):
    global ticker_data
    

    try:




        ages = ticker_data[ticker][0]
        prices = ticker_data[ticker][1]
        dpg.add_line_series(x=ages, y=prices, parent="plot_y_axis", tag=f"{ticker}_plot")
        dpg.fit_axis_data('plot_x_axis')
        dpg.fit_axis_data('plot_y_axis')

        dpg.bind_item_theme(f"{ticker}_plot", plot_theme)

        plot_simulated_all(ticker)
        log_message(f"Displaying price history for {ticker}")
    except:
        log_message(f"Error displaying price history for {ticker}")

def remove_from_plot(ticker):
    dpg.delete_item(f"{ticker}_plot")
    remove_plot_simulated_all(ticker)
    log_message(f"Hiding price history for {ticker}")
    
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def floor_text_whole_number(sender, app_data, user_data):
    try:
        num = float(app_data)
        floored = math.floor(num)
        floored_string = str(floored)
        dpg.set_value(sender, floored_string)
    except:
        dpg.set_value(sender, '0')

def log_message(message):
    dpg.add_text(f"{now()}: " + message, parent="log_window")
    scroll_to_window_bottom("log_window")

def scroll_to_window_bottom(window_tag):
    dpg.set_y_scroll(item=window_tag, value = dpg.get_y_scroll_max(window_tag) + 100.0)

def request_data(list_txt_path):
    list_txt_path = os.path.join(os.getcwd(), TICKERS_LIST_FOLDER, list_txt_path)
    completed_tickers = []
    total_tickers = 0

    try:
        csv_files = os.listdir(os.path.join(os.getcwd(), GENERATED_DATA_PATH, TODAY))
        for f in csv_files:
            if f[-4:] == ".csv":
                completed_tickers.append(f[:-4])

    except:
        log_message(f"No data found for {TODAY}")
    
    if len(completed_tickers) != 0:
        log_message(f"{TODAY} data already found for {len(completed_tickers)} tickers")

    token_index = 0 #Keep track of which token we are using, use next token when limit has been reached for current token
    with open(list_txt_path, 'r') as f2:

        token = tokens[token_index]

        lines = f2.readlines()
        total_tickers = len(lines)

        log_message(f"Beginning historical data retrieval for {len(lines) - len(completed_tickers)} tickers...")
        log_message(f"Using token {token}")
        i = 0
        while i < (len(lines)):
            
            exit_code = 0
            ticker = lines[i].rstrip()
            print(ticker)
            if ticker not in completed_tickers:
                exit_code = request_ticker_historical(ticker, token)
                if exit_code > 0:
                    token_index += 1
                    if token_index >= len(tokens):
                        log_message("Expended all tokens. Try again later")
                        break
                    else:
                        token = tokens[token_index]
                        log_message(f"Using token {token}")
                        continue
                else:
                    completed_tickers.append(ticker)
                    i += 1
            else:
                log_message(f"Up-to-date data already found for {ticker}, skipping...")
                i += 1

    log_message(f"{len(completed_tickers)}/{total_tickers} tickers completed")
    check_all_tickers_status()


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
        log_message(f"{response.text}")
        return 1
    try:
        with open(f"{GENERATED_DATA_PATH}/{TODAY}/{ticker}.csv", 'w') as f:
            bytes_written = f.write(response.text)
            log_message(f"Retrieved {ticker}, sucessfully wrote {int(bytes_written/1024)}KB")
            return 0
    except:
        log_message(f"{response.text}")
        return 1




running = True

while running:
    
    dpg.create_context()

    with dpg.theme() as disabled_theme:
        with dpg.theme_component(dpg.mvButton, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 30, 30, 255))  # Dark grey
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (30, 30, 30, 255))  # Same as button
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 30, 30, 255))  # No change
            dpg.add_theme_color(dpg.mvThemeCol_Text, (70, 70, 70, 255))


    with dpg.theme() as plot_theme:
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, (125, 145, 160), category=dpg.mvThemeCat_Plots)

    dpg.create_viewport(x_pos=int(SCREEN_X * 0.125), y_pos=int(SCREEN_Y * 0.125),title='StockToy', width=WIDTH, height=HEIGHT, decorated=True)



    with dpg.window(no_close=True,
                    no_collapse=True,
                    tag="main_window") as main_window:
        pass

    with dpg.window(no_collapse=True,
                    no_title_bar=True,
                    no_close=True,
                    tag="price_history_window") as price_history_window:
        
        with dpg.menu_bar():

                with dpg.menu(label="Menu"):

                    dpg.add_menu_item(label="Save Layout", callback=lambda : dpg.configure_item("save_ini_popup", show=True))
                    dpg.add_menu_item(label="Load Layout", callback=lambda : create_layout_options_window())
                    dpg.add_menu_item(label="Quit", callback=lambda : dpg.destroy_context())
                    
        with dpg.plot(label="Price History", height=-1, width=-1):
            dpg.add_plot_axis(dpg.mvXAxis, label="Days since today", tag = "plot_x_axis", invert=True)          
            dpg.add_plot_axis(dpg.mvYAxis, label="Closing price (USD)", tag = "plot_y_axis")

    
    with dpg.window(no_collapse=True,
                    no_title_bar=True,
                    no_close=True,
                    tag="log_window",
                    label="Logger") as log_window:
        pass

    with dpg.window(no_collapse=True,
                    no_close=True,
                    tag="simulation_settings_window") as simulation_settings_window:
        dpg.add_checkbox(label="Enable Simulation", callback=toggle_item, user_data="forecasting_settings")
        dpg.add_separator()

        dpg.add_separator()
        with dpg.group(tag="metrics_settings", enabled=False):
            dpg.add_text("Metrics")
            dpg.add_separator()
            dpg.add_button(label="Calculate metrics")
            dpg.add_checkbox(label="temp")
            dpg.add_checkbox(label="temp")
            dpg.add_checkbox(label="temp")
            dpg.add_checkbox(label="temp")


        dpg.add_separator()
        with dpg.group(tag="predictions_settings", enabled=False):
            dpg.add_text("Predictions")
            dpg.add_separator()
            dpg.add_button(label="Predict prices")
            dpg.add_checkbox(label="temp")
            dpg.add_checkbox(label="temp")
            dpg.add_checkbox(label="temp")
            dpg.add_checkbox(label="temp")

        dpg.add_separator()
        with dpg.group(tag="forecasting_settings", enabled=False):
            dpg.add_text("Forecasting")
            dpg.add_separator()
            dpg.add_button(label="Start forecasting", callback=lambda : simulate_price_change(tickers_toggled, dpg.get_value("forecasting_count_textbox"), dpg.get_value("forecasting_length_textbox")))
            dpg.add_combo(label="Forecasting method")
            dpg.add_input_text(label="Forecasting length (days)", tag = "forecasting_length_textbox", decimal=True, callback=floor_text_whole_number)
            dpg.add_input_text(label="Forecasting count", tag = "forecasting_count_textbox", decimal=True, callback=floor_text_whole_number)
            dpg.bind_item_theme("forecasting_settings", disabled_theme)


    with dpg.window(no_collapse=True,
                    no_close=True,
                    label="Tickers",
                    tag="ticker_window") as ticker_window:
        dpg.add_separator()
        with dpg.group(horizontal=True):
            text_files = [f for f in os.listdir(os.path.join(os.getcwd(), "tickers")) if f[-4:] == ".txt"]
            dpg.add_text("Choose ticker list")
            dpg.add_combo(text_files, fit_width=True, tag="selected_ticker", callback = lambda : update_tickers_file(dpg.get_value("selected_ticker")))
            dpg.add_button(label="Confirm", callback=lambda : create_tickers_menu(dpg.get_value("selected_ticker")))

        with dpg.group(horizontal=True):
            dpg.add_button(label="Request Data", tag="request_data_button",enabled=False, callback=lambda : request_data(tickers_file))
        
        dpg.bind_item_theme("request_data_button", disabled_theme)

        with dpg.tooltip("request_data_button", tag = "disabled_request_tooltip"):
            dpg.add_text("You must select a ticker list before requesting data")

        dpg.add_separator()

    with dpg.window(pos=[WIDTH/2, HEIGHT/2], show=False, tag="save_ini_popup"):
        dpg.add_text("Layout will be saved as the following:")
        dpg.add_separator()
        dpg.add_input_text(tag="save_ini_text", default_value="default.ini")
        with dpg.group(horizontal=True):
            dpg.add_button(label="Save", width=75, callback=save_ini)
            dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.configure_item("save_ini_popup", show=False))

    with dpg.window(pos=[WIDTH/2, HEIGHT/2], modal=True, show=False, tag="invalid_filename_popup", no_title_bar=True):
        dpg.add_text("Filename must end in '.ini'")
        dpg.add_button(label="Okay", width=75, callback=lambda: dpg.configure_item("invalid_filename_popup", show=False))

    dpg.configure_app(init_file=init)
    dpg.configure_app(docking=True, docking_space=True)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    dpg.set_primary_window("main_window", True)
    log_message(f"Successfully started StockToy")
    load_tokens()

    dpg.start_dearpygui()
    dpg.destroy_context()
