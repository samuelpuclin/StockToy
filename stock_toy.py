import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import os
from datetime import datetime
from datetime import date
from pyautogui import size

SCREEN_X = size()[0]
SCREEN_Y = size()[1]

WIDTH = int(SCREEN_X * 0.75)
HEIGHT = int(SCREEN_Y * 0.75)

init = "default.ini"
tickers = {}


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

def create_layout_options_window():
    temp = dpg.add_window(pos=[WIDTH/2, HEIGHT/2])
    dpg.add_text("Load layout:", parent=temp)
    dpg.add_separator(parent=temp)
    ini_files = get_ini_files()
    for file in ini_files:
        dpg.add_button(parent=temp, label=file, callback=load_init)


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
        
        for line in lines:
            with dpg.group(parent="ticker_checkboxes", tag=line + "_group", horizontal=True):
                dpg.add_checkbox(label=line,parent=line + "_group", callback=toggle_tickers)
                dpg.add_text("Latest data available: ", parent=line + "_group", color=[200,200,0,255])


            #Update the tickers dict and by default set them all as no data
            tickers[line] = None
        #dpg.add_checkbox(label=f,parent=ticker_window)

def check_ticker_status():

    global tickers
    test = 0
    data_path = os.path.join(os.getcwd(), "generated_data")
    directories = os.listdir(data_path)
    for d in directories:
        dir_path = (os.path.join(data_path, d))
        if os.path.isdir(dir_path):

            #Get data age in days
            age = (datetime.today() - datetime.strptime(d, "%Y-%m-%d")).days
            print(age)

            files = os.listdir(dir_path)
            for f in files:
                if f[-4:] == ".csv":
                    ticker = f[:-4]
                    tickers[ticker] = age
                    test += 1
    
    for t in tickers:
        print(f"{t} : {tickers[t]}")

    

def toggle_tickers(sender, app_data):
    global tickers
    ticker = dpg.get_item_label(sender)
    if dpg.get_value(sender): #Checkbox ticked
        tickers.update(ticker)
    else:
        tickers.remove(ticker)

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
                    dpg.add_menu_item(label="Quit", callback=lambda : dpg.destroy_context())
                    
        with dpg.plot(label="Price History", height=-1, width=-1):
            dpg.add_plot_axis(dpg.mvXAxis, label="x")          
            with dpg.plot_axis(dpg.mvYAxis, label="y"):
                #dpg.add_line_series(x,y)
                pass
        


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
