#!/usr/bin/env python3
"""
    *******************************************************************************************
    MLSMatrixBot.
    Author: Ali Toori, Full Stack Python Developer [Bot Builder]
    Website: https://botflocks.com
    *******************************************************************************************
"""
import json
import logging.config
import os
import pickle
import random
import time
from datetime import datetime
from multiprocessing import freeze_support
from pathlib import Path
from time import sleep
import pyautogui
import ntplib
import pandas as pd
import pyfiglet
from random import randint

import pyperclip
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class MLSMatrixBot:
    def __init__(self):
        self.PROJECT_ROOT = Path(os.path.abspath(os.path.dirname(__file__)))
        self.file_settings = str(self.PROJECT_ROOT / 'MLSRes/Settings.json')
        self.directory_downloads = str(self.PROJECT_ROOT / 'MLSRes/Downloads/')
        self.file_lands = self.PROJECT_ROOT / 'MLSRes/LandProperties.csv'
        self.MLS_HOME_URL = "https://ntrdd.mlsmatrix.com/"
        self.MLS_SEARCH_URL = "https://ntrdd.mlsmatrix.com/Matrix/Search/Land/Detailed"
        self.settings = self.get_settings()
        self.account = self.settings["Settings"]
        self.LOGGER = self.get_logger()
        self.driver = None
        self.logged_in = False

    # Get self.LOGGER
    @staticmethod
    def get_logger():
        """
        Get logger file handler
        :return: LOGGER
        """
        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,
            'formatters': {
                'colored': {
                    '()': 'colorlog.ColoredFormatter',  # colored output
                    # --> %(log_color)s is very important, that's what colors the line
                    'format': '[%(asctime)s,%(lineno)s] %(log_color)s[%(message)s]',
                    'log_colors': {
                        'DEBUG': 'green',
                        'INFO': 'cyan',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'bold_red',
                    },
                },
                'simple': {
                    'format': '[%(asctime)s,%(lineno)s] [%(message)s]',
                },
            },
            "handlers": {
                "console": {
                    "class": "colorlog.StreamHandler",
                    "level": "INFO",
                    "formatter": "colored",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "simple",
                    "filename": "MLSMatrixBot.log",
                    "maxBytes": 50 * 1024 * 1024,
                    # "backupCount": 3
                },
            },
            "root": {"level": "INFO",
                     "handlers": ["console", "file"]
                     }
        })
        return logging.getLogger()

    @staticmethod
    def enable_cmd_colors():
        # Enables Windows New ANSI Support for Colored Printing on CMD
        from sys import platform
        if platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    @staticmethod
    def banner():
        pyfiglet.print_figlet(text='____________ BinanceBot\n', colors='RED')
        print('Author: Ali Toori\n'
              'Website: https://botflocks.com/\n'
              '************************************************************************')
        # Get settings from Setting.json file

    def get_settings(self):
        """
        Creates default or loads existing settings file.
        :return: settings
        """
        if os.path.isfile(self.file_settings):
            with open(self.file_settings, 'r') as f:
                settings = json.load(f)
            return settings
        settings = {"Settings": {
            "UserName": "Please Enter Your MLSMatrix Username",
            "Password": "Please Enter Your Password",
            "Counties": ["Dallas county", "Tarrant county", "Fannin county"],
            "BannedOwners": ["LLC", "Corp"]}}
        with open(self.file_settings, 'w') as f:
            json.dump(settings, f, indent=4)
        with open(self.file_settings, 'r') as f:
            settings = json.load(f)
        return settings

    # Get random user-agent
    def get_user_agent(self):
        file_uagents = self.PROJECT_ROOT / 'MLSRes/user_agents.txt'
        with open(file_uagents) as f:
            content = f.readlines()
        u_agents_list = [x.strip() for x in content]
        return random.choice(u_agents_list)

    # Get web driver
    def get_driver(self, proxy=None, headless=False):
        # For absolute chromedriver path
        DRIVER_BIN = str(self.PROJECT_ROOT / "MLSRes/bin/chromedriver.exe")
        service = Service(executable_path=DRIVER_BIN)
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--incognito")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features")
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        prefs = {f'profile.default_content_settings.popups': 0,
                 f'download.default_directory': f'{self.directory_downloads}',  # IMPORTANT - ENDING SLASH V IMPORTANT
                 "directory_upgrade": True,
                 "credentials_enable_service": False,
                 "profile.password_manager_enabled": False}
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument(F'--user-agent={self.get_user_agent()}')
        # options.add_argument('--headless')
        if proxy is not None:
            options.add_argument(f"--proxy-server={proxy}")
        if headless:
            options.add_argument('--headless')
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    # Finish and quit browser
    def finish(self):
        try:
            self.LOGGER.info(f'Closing browser')
            self.driver.close()
            self.driver.quit()
        except WebDriverException as exc:
            self.LOGGER.info(f'Issue while closing browser: {exc.args}')

    @staticmethod
    def wait_until_visible(driver, css_selector=None, element_id=None, name=None, class_name=None, tag_name=None, xpath=None, duration=10000, frequency=0.01):
        if css_selector:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
        elif element_id:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.ID, element_id)))
        elif name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.NAME, name)))
        elif class_name:
            WebDriverWait(driver, duration, frequency).until(
                EC.visibility_of_element_located((By.CLASS_NAME, class_name)))
        elif tag_name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.TAG_NAME, tag_name)))
        if xpath:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.XPATH, xpath)))

    # Login to the website
    def login_mls(self, driver):
        user_name = str(self.account["UserName"])
        password = str(self.account["Password"])
        self.LOGGER.info(f'Signing-in to the MLS Matrix')
        self.LOGGER.info(f"Requesting MLSMatrix: {str(self.MLS_HOME_URL)}")
        driver.get(self.MLS_HOME_URL)
        try:
            self.LOGGER.info(f"Signing-in normally")
            # self.LOGGER.info(f"Requesting MLSMatrix: {str(self.MLS_HOME_URL)}")
            # driver.get(self.MLS_HOME_URL)
            self.LOGGER.info(f"Waiting for login fields to become visible")
            self.wait_until_visible(driver=driver, css_selector='[id="clareity"]')
            # Filling login fields
            self.LOGGER.info(f"Filling username: {user_name}")
            sleep(1)
            pyautogui.hotkey('esc')
            sleep(1)
            driver.find_element(By.CSS_SELECTOR, '[id="clareity"]').send_keys(user_name)
            self.LOGGER.info(f"Filling password: {password}")
            sleep(1)
            driver.find_element(By.CSS_SELECTOR, '[id="security"]').send_keys(password)
            # pyautogui.write(password)
            self.LOGGER.info(f"Signing in")
            sleep(1)
            # Clicking button login
            driver.find_element(By.CSS_SELECTOR, '[id="loginbtn"]').click()
            self.LOGGER.info(f"Waiting for MLSMatrix profile to become visible")
            self.wait_until_visible(driver=driver, css_selector='[id="appDetailMatrix"]')
            self.LOGGER.info(f"Profile has been visible")
            self.LOGGER.info(f"Successfully logged in")
            return True
        except WebDriverException as ec:
            self.LOGGER.error(f"Exception while signing-in]:" + str(ec.msg))
            return False

    # Returns center of the screen
    @staticmethod
    def get_screen_center():
        height = pyautogui.size().width
        width = pyautogui.size().height
        center_x, center_y = int(height / 2), int(width / 2)
        return center_x, center_y

    # Scrapes followers of an MLSMatrix account
    def get_properties(self, driver):
        banned_owners = self.account["BannedOwners"]
        self.LOGGER.info(f"Requesting: {self.MLS_SEARCH_URL}")
        driver.get(self.MLS_SEARCH_URL)
        # Wait for map
        self.LOGGER.info(f"Waiting for map")
        self.wait_until_visible(driver=driver, css_selector='[class="fal fa-map"]')
        driver.find_element(By.CSS_SELECTOR, '[class="fal fa-map"]').click()
        self.LOGGER.info(f"Waiting for search box")
        self.wait_until_visible(driver=driver, css_selector='[id="m_ga_m_tb"]')
        self.wait_until_visible(driver=driver, css_selector='[class="fal fa-location"]')
        recenter_loc = driver.find_element(By.CSS_SELECTOR, '[class="fal fa-location"]').location
        print(f'Recenter location: {recenter_loc}')
        y_upper = recenter_loc['y'] + 110
        y_lower = recenter_loc['y'] + 350
        coordinates = [[randint(172, 1250), randint(y_upper, y_lower)] for i in range(40)]
        print(f'Coords: {coordinates}')
        center_x, center_y = self.get_screen_center()
        for search in self.account["Counties"]:
            self.LOGGER.info(f"Searching in: {search}")
            driver.find_element(By.CSS_SELECTOR, '[id="m_ga_m_tb"]').send_keys(search)
            driver.find_element(By.CSS_SELECTOR, '[id="m_ga_m_tb"]').send_keys(Keys.ENTER)
            self.wait_until_visible(driver=driver, css_selector='[aria-label="Map"]')
            map_element = driver.find_element(By.CSS_SELECTOR, '[aria-label="Map"]')
            map_element.click()
            sleep(3)
            # Move to the right in the map
            # ActionChains(driver).drag_and_drop_by_offset(source=map_element, xoffset=170, yoffset=300)
            for i in range(100):
                driver.find_element(By.CSS_SELECTOR, '[aria-label="Map"]').send_keys(Keys.ARROW_LEFT)
                driver.find_element(By.CSS_SELECTOR, '[aria-label="Map"]').send_keys(Keys.ARROW_LEFT)
                driver.find_element(By.CSS_SELECTOR, '[aria-label="Map"]').send_keys(Keys.ARROW_LEFT)
            # Zoom-in the map to 6 points
            self.LOGGER.info(f"Zooming in")
            for i in range(9):
                driver.find_element(By.CSS_SELECTOR, '[aria-label="Map"]').send_keys(Keys.ADD)
                sleep(0.1)
            # map_location = driver.find_element(By.CSS_SELECTOR, '[aria-label="Map"]').location
            # self.LOGGER.info(f"Map location: {map_location}")
            # pyautogui.moveTo(x=map_location["x"], y=map_location["y"])
            while True:
                sleep(1)
                coord = random.choice(coordinates)
                pyautogui.moveTo(x=coord[0], y=coord[1])
                self.LOGGER.info(f"Selecting property at: {coord}")
                pyautogui.click(x=coord[0], y=coord[1], button='left')
                try:
                    self.wait_until_visible(driver=driver, css_selector='[class="formula heading2 field d271m7"]', duration=10)
                    address_a = driver.find_element(By.CSS_SELECTOR, '[class="formula heading2 field d271m7"]').text
                    address_b = driver.find_element(By.CSS_SELECTOR, '[class="formula field d271m8"]').text
                    property_address = f'{address_a}, {address_b}'
                    if os.path.isfile(self.file_lands):
                        df = pd.read_csv(self.file_lands, index_col=None)
                        if property_address in df['Property Address'].values:
                            self.LOGGER.info(f"Property already scraped: {property_address}")
                            continue
                except:
                    sleep(1)
                    continue
                try:
                    self.wait_until_visible(driver=driver, css_selector='[class="formula wrapped-field field d271m19"]', duration=5)
                    owner_name = driver.find_element(By.CSS_SELECTOR, '[class="formula wrapped-field field d271m19"]').text
                    prop_table = driver.find_elements(By.CSS_SELECTOR, '[class="d271m2"]')[1]
                    structure = driver.find_element(By.CSS_SELECTOR, '[class="formula wrapped-field field d271m18"]').text
                    acres = prop_table.find_elements(By.TAG_NAME, 'tr')[8].text
                    # print(f'Acres: {acres}')
                    acres = float(str(acres).replace(',', '').split(' ')[-2])
                    self.LOGGER.info(f"Property details: Address: {property_address}, Owner Name: {owner_name}, Structure: {structure}, Area: {acres} Acres")
                    banned = [True for band in owner_name.split(' ') if band in banned_owners]
                    if len(banned) > 0:
                        self.LOGGER.info(f"Property didn't match the filters, moving on ...")
                        continue
                    if acres <= 1 or 'SqFt' in structure:
                        self.LOGGER.info(f"Property didn't match the filters, moving on ...")
                        continue
                except:
                    continue
                try:
                    last_sold = driver.find_elements(By.CSS_SELECTOR, '[class="formula wrapped-field field d271m18"]')[1].text
                    if 'Last sold on' in last_sold and int(last_sold[-4:]) > 2019:
                        self.LOGGER.info(f"Property last sold: {last_sold}, moving on")
                        continue
                except:
                    sleep(1)
                    pass
                try:
                    # CLick on Tax link
                    self.LOGGER.info(f"Property matched the filters, scraping property details ...")
                    self.wait_until_visible(driver=driver, css_selector='[title="Tax Full"]', duration=5)
                    driver.find_element(By.CSS_SELECTOR, '[title="Tax Full"]').click()
                    address_split = str(address_b).replace(',', '').split(' ')
                    prop_city = address_split[-3]
                    prop_state = address_split[-2]
                    prop_zip_code = address_split[-1]
                except:
                    sleep(1)
                    continue
                self.LOGGER.info(f"Waiting for owner name ...")
                self.wait_until_visible(driver=driver, css_selector='[id="wrapperTable"]', duration=10)
                sleep(1.5)
                # View page source
                pyautogui.hotkey('ctrl', 'u')
                sleep(1)
                # Select all
                pyautogui.hotkey('ctrl', 'a')
                sleep(1)
                # Copy
                pyautogui.hotkey('ctrl', 'c')
                # Close current tab
                pyautogui.hotkey('ctrl', 'w')
                sleep(1)
                pyautogui.hotkey('ctrl', 'w')
                source_code = pyperclip.paste()
                sleep(1)
                # print(f'Source code from clipboard: {source_code}')
                soup = BeautifulSoup(source_code, 'lxml')
                try:
                    owner_name = soup.find_all('span', {'class': 'd-fontSize--smaller d-textStrong'})[0].get_text()
                    mailing_address = soup.find_all('span', {'class': 'd-fontSize--smaller d-textStrong'})[1].get_text()
                    owner_city_state = soup.find_all('span', {'class': 'd-fontSize--smaller d-textStrong'})[2].get_text()
                    owner_state = str(owner_city_state).split(' ')[1]
                    owner_city = str(owner_city_state).split(' ')[0]
                    owner_zip_code = soup.find_all('span', {'class': 'd-fontSize--smaller d-textStrong'})[3].get_text()
                    prop_dict = {"Owners Name": owner_name, "Property Address": property_address, "Property State": prop_state, "Property City": prop_city, "Property Zip Code":prop_zip_code,
                                 "Mailing Address": mailing_address, "Mailing State": owner_state, "Mailing City": owner_city, "Mailing Zip Code": owner_zip_code}
                    data_frame = pd.DataFrame([prop_dict])
                    self.LOGGER.info(f"Saving property: {prop_dict}")
                    if not os.path.isfile(self.file_lands):
                        data_frame.to_csv(self.file_lands, index=False)
                    else:  # else if exists so append without writing the header
                        data_frame.to_csv(self.file_lands, mode='a', header=False, index=False)
                    self.LOGGER.info(f"Property has been saved to: {self.file_lands}")
                except:
                    pass

    def main(self):
        freeze_support()
        self.enable_cmd_colors()
        # Print ASCII Art
        print('************************************************************************\n')
        pyfiglet.print_figlet('____________                   MLSBot ____________\n', colors='RED')
        print('Author: Ali Toori, Python Developer [Bot Builder]\n'
              'Website: https://botflocks.com/\n************************************************************************')
        PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
        PROJECT_ROOT = Path(PROJECT_ROOT)
        self.LOGGER.info(f'Launching MLSBot ...')
        self.LOGGER.info(f"Starting Scraper ...")
        if self.driver is None:
            self.driver = self.get_driver()
        if not self.logged_in:
            self.logged_in = self.login_mls(driver=self.driver)
        self.get_properties(driver=self.driver)


if __name__ == '__main__':
    mls_bot = MLSMatrixBot()
    mls_bot.main()
