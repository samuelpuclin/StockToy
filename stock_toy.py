import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import os
import pandas as pd
from datetime import datetime
from datetime import date
from pyautogui import size

SCREEN_X = size()[0]
SCREEN_Y = size()[1]

WIDTH = int(SCREEN_X * 0.75)
HEIGHT = int(SCREEN_Y * 0.75)

GREEN = [0,200,0,255]
YELLOW = [200,200,0,255]
RED = [200,0,0,255]

init = "default.ini"
ticker_data_age = {}
tickers_toggled = set()
tokens = []

ticker_data = {}

def load_init(sender, app_data):
    print(dpg.get_item_label(sender))
    global init
    init = dpg.get_item_label(sender)
    dpg.stop_dearpygui()
    
def save_ini(sender, app_data, user_data):
    filename = dpg.get_value("save_ini_text")
    if filename[-4:] == ".ini":
        dpg.configure_item("save_ini_popup", show=False)
        dpg.save_init_file(filename)
    else:
        dpg.configure_item("invalid_filename_popup", show=True)
        print(dpg.get_item_configuration("invalid_filename_popup"))

def get_ini_files():
    files = [f for f in os.listdir(os.getcwd()) if f[-4:] == ".ini"]
    return files

def get_api_files():
    token_folder_path = os.path.join(os.getcwd(), "api_tokens")
    files = [f for f in os.listdir(token_folder_path) if f[-4:] == ".txt"]
    print(files)
    return files

def create_layout_options_window():
    temp = dpg.add_window(pos=[WIDTH/2, HEIGHT/2])
    dpg.add_text("Load layout:", parent=temp)
    dpg.add_separator(parent=temp)
    ini_files = get_ini_files()
    for file in ini_files:
        dpg.add_button(parent=temp, label=file, callback=load_init)

def create_api_token_options_window():
    temp = dpg.add_window(pos=[WIDTH/2, HEIGHT/2])

    global tokens

    files = get_api_files()
    for file in files:
        with open(os.path.join(os.getcwd(), "api_tokens", file), 'r') as f:
            tokens_temp = [line.rstrip() for line in f]
            tokens.extend(tokens_temp)
            tokens = list(dict.fromkeys(tokens))

    dpg.add_text("Choose API token: ", parent=temp)
    dpg.add_separator(parent=temp)

    #delete before remaking so no conflicting ids
    dpg.delete_item("selected_token")
    dpg.add_combo(tokens,fit_width=True, tag="selected_token",parent=temp)

def create_tickers_menu(ticker_file):
    if ticker_file != "":
        dpg.hide_item("disabled_request_tooltip")
        dpg.hide_item("disabled_check_tooltip")
        with open(os.path.join("tickers", ticker_file), "r") as f:
            lines = [line.rstrip() for line in f]
            if len(lines) >= 1:
                dpg.configure_item("request_data_button", enabled=True)
                dpg.configure_item("check_data_button", enabled=True)
            else:
                dpg.configure_item("request_data_button", enabled=False)
                dpg.configure_item("check_data_button", enabled=False)

        dpg.delete_item("ticker_checkboxes")
        dpg.add_group(parent="ticker_window", tag="ticker_checkboxes")
        
        for ticker in lines:
            with dpg.group(parent="ticker_checkboxes", tag=ticker + "_group", horizontal=True):
                dpg.add_checkbox(parent=ticker + "_group", callback=toggle_tickers, user_data=ticker)
                dpg.add_text(ticker,parent=ticker + "_group", tag=ticker + "_text")
            #Update the tickers dict and by default set them all as no data
            ticker_data_age[ticker] = None
        #dpg.add_checkbox(label=f,parent=ticker_window)

def check_ticker_status():

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
            else:
                dpg.configure_item(checkbox_text, color=YELLOW)
        else:
            dpg.configure_item(checkbox_text, color=RED)

    for t in ticker_data_age:
        print(f"{t} : {ticker_data_age[t]}")

    csv_to_plottable_all()
    

def csv_to_plottable_all():

    global ticker_data

    folders = [f for f in os.listdir(os.path.join(os.getcwd(), "generated_data")) if os.path.isdir(os.path.join(os.getcwd(), "generated_data", f))]

    for key in ticker_data_age:
        for f in folders:
            folder_age = (datetime.today() - datetime.strptime(f, "%Y-%m-%d")).days
            if folder_age == ticker_data_age[key]:
                df = pd.read_csv(os.path.join(os.getcwd(), "generated_data", f, f"{key}.csv"))
                dates = df['date']
                prices = df['close']
                ages = dates.apply(date_to_age)
                plot_data = [ages, prices]
                ticker_data.update({key : plot_data})
    # for key, value in ticker_data.items() :
    #     print (key, value)


def date_to_age(date):
    return (datetime.today() - datetime.strptime(date, "%Y-%m-%d")).days

def toggle_tickers(sender, app_data, user_data):
    global tickers_toggled
    ticker = user_data
    if dpg.get_value(sender): #Checkbox ticked
        tickers_toggled.add(ticker)
        print(ticker)
        add_to_plot(ticker)
    else:
        tickers_toggled.remove(ticker)
        remove_from_plot(ticker)

def add_to_plot(ticker):
    global ticker_data
    #for key, value in ticker_data.items():
    ages = pd.Series.to_list(ticker_data[ticker][0])
    prices = pd.Series.to_list(ticker_data[ticker][1])
    dpg.add_line_series(x=ages, y=prices, parent="plot_y_axis", tag=f"{ticker}_plot")
    dpg.fit_axis_data('plot_x_axis')
    dpg.fit_axis_data('plot_y_axis')
    print("added?")

def remove_from_plot(ticker):
    dpg.delete_item(f"{ticker}_plot")


running = True

while running:
    print(init)
    
    dpg.create_context()
    
    dpg.create_viewport(x_pos=int(SCREEN_X * 0.125), y_pos=int(SCREEN_Y * 0.125),title='StockToy', width=WIDTH, height=HEIGHT, decorated=True)



    with dpg.theme() as disabled_theme:
        with dpg.theme_component(dpg.mvButton, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 30, 30, 255))  # Dark grey
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (30, 30, 30, 255))  # Same as button
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 30, 30, 255))  # No change
            dpg.add_theme_color(dpg.mvThemeCol_Text, (70, 70, 70, 255))



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
                    dpg.add_menu_item(label="Configure API Tokens", callback=lambda : create_api_token_options_window())
                    dpg.add_menu_item(label="Quit", callback=lambda : dpg.destroy_context())
                    
        with dpg.plot(label="Price History", height=-1, width=-1):
            dpg.add_plot_axis(dpg.mvXAxis, label="x", tag = "plot_x_axis", invert=True)          
            dpg.add_plot_axis(dpg.mvYAxis, label="y", tag = "plot_y_axis")

        


    with dpg.window(no_collapse=True,
                    no_close=True,
                    label='Simulation Settings',
                    tag="simulation_settings_window") as simulation_settings_window:
        pass
        
    with dpg.window(no_collapse=True,
                    no_close=True,
                    label="Tickers",
                    tag="ticker_window") as ticker_window:
        dpg.add_separator()
        with dpg.group(horizontal=True):
            text_files = [f for f in os.listdir(os.path.join(os.getcwd(), "tickers")) if f[-4:] == ".txt"]
            dpg.add_text("Choose ticker list")
            dpg.add_combo(text_files, fit_width=True, tag="selected_ticker")
            dpg.add_button(label="Confirm", callback=lambda : create_tickers_menu(dpg.get_value("selected_ticker")))

        with dpg.group(horizontal=True):
            dpg.add_button(label="Request Data", tag="request_data_button",enabled=False)
            dpg.add_button(label="Check Data", tag="check_data_button",enabled=False, callback=lambda: check_ticker_status())
        
        dpg.bind_item_theme("request_data_button", disabled_theme)
        dpg.bind_item_theme("check_data_button", disabled_theme)

        with dpg.tooltip("request_data_button", tag = "disabled_request_tooltip"):
            dpg.add_text("You must select a ticker list before requesting data")

        with dpg.tooltip("check_data_button", tag = "disabled_check_tooltip"):
            dpg.add_text("You must select a ticker list before checking data")
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

    dpg.start_dearpygui()
    dpg.destroy_context()
