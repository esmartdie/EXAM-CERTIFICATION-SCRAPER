# Copyright (c) 2025 Diego Martins
# Licensed under the MIT License. See LICENSE file in the project root for details.
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


def setup_browser():
    """
    Configures and initializes a Selenium WebDriver instance.

    Returns:
        WebDriver: Configured Chrome WebDriver instance.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("start-maximized")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    webdriver_path = r"driver/chromedriver.exe"
    browser = webdriver.Chrome(service=Service(webdriver_path), options=options)
    return browser