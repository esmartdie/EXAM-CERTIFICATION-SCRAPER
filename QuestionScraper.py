# Copyright (c) 2025 Diego Martins
# Licensed under the MIT License. See LICENSE file in the project root for details.

import random
import os
import json
import time
from FileManager import FileManager
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def load_page(browser, url, wait_time=10):
    """
    Loads a web page and waits for the specified element to be present.

    Args:
        browser (WebDriver): Selenium WebDriver instance.
        url (str): URL of the page to load.
        wait_time (int): Maximum time to wait for the element (default: 10 seconds).

    Returns:
        BeautifulSoup: Parsed HTML content of the page.

    Raises:
        Exception: If the page cannot be loaded or the element is not found.
    """
    try:
        browser.get(url)
        WebDriverWait(browser, wait_time).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-discussion-header"))
        )
        return BeautifulSoup(browser.page_source, "html.parser")
    except Exception as e:
        raise Exception(f"Error al cargar la página {url}: {str(e)}")


def scrape_page(soup):
    """
    Extracts question data from a BeautifulSoup object representing a loaded page.

    Args:
        soup (BeautifulSoup): Parsed HTML content of the page.

    Returns:
        dict: Extracted question data including question text, choices, images, and answers.

    Raises:
        Exception: If required elements are not found in the page.
    """
    try:
        question_number = extract_question_number(soup)
        question_body = soup.find("div", class_="question-body mt-3 pt-3 border-top")
        if not question_body:
            raise Exception("Question body not found.")

        question_text_element = question_body.find("p", class_="card-text")
        if not question_text_element:
            raise Exception("Question text not found.")
        question_text = question_text_element.get_text(strip=True)

        question_image_src = [
            format_image_url(img_tag['src'])
            for img_tag in question_text_element.find_all("img")
        ]

        answer_section = question_body.find("div", class_="card-text question-answer bg-light white-text")
        if answer_section:
            answer_image_src = [
                format_image_url(img_tag['src'])
                for img_tag in answer_section.find_all("img")
            ]
            answer_image_text = " ".join(answer_section.stripped_strings)
        else:
            answer_image_src = []
            answer_image_text = ""

        choices_container = question_body.find("div", class_="question-choices-container")
        choices = []
        if choices_container:
            for li in choices_container.find_all("li"):
                choice_letter = li.find("span", class_="multi-choice-letter")["data-choice-letter"]
                choice_text = li.get_text(strip=True).replace("Most Voted", "").strip()  # Clean text
                is_correct = li.get("class") and "correct-hidden" in li.get("class")
                choices.append({
                    "letter": choice_letter,
                    "text": choice_text,
                    "correct": is_correct
                })

        return {
            "question_number": question_number,
            "question_text": question_text,
            "choices": choices,
            "question_image_src": question_image_src,
            "answer_image_text": answer_image_text,
            "answer_image_src": answer_image_src
        }
    except Exception as e:
        raise Exception(f"Error processing page data: {str(e)}")


def format_image_url(img_src):
    """
    Formats an image URL, ensuring it is complete and valid.

    Args:
        img_src (str): Source URL of the image.

    Returns:
        str: Complete image URL.

    Raises:
        ValueError: If the URL format is unrecognized.
    """
    if img_src.startswith("/"):
        return f"https://www.examtopics.com{img_src}"
    elif img_src.startswith("http"):
        return img_src
    else:
        raise ValueError(f"Unrecognized image URL format: {img_src}")


def extract_question_number(soup):
    """
    Extracts the question number from the question text.

    Args:
        soup (BeautifulSoup): Parsed HTML content of the page.

    Returns:
        int: Extracted question number.

    Raises:
        ValueError: If the question number cannot be extracted.
    """
    try:
        header_div = soup.find("div", class_="question-discussion-header")
        inner_div = header_div.find("div")
        return inner_div.get_text(strip=True).split("Topic #:")[0].strip()
    except (IndexError, ValueError):
        raise ValueError(f"Could not extract question number")


def scrape_question_info(browser, file_manager):
    """
    Orchestrates the scraping of question information, updating progress in CSV and JSON files.

    Args:
        browser (WebDriver): Selenium WebDriver instance.
        file_manager (FileManager): Instance of FileManager for handling CSV and JSON files.

    Returns:
        None
    """
    user_requirements = file_manager.get_input_json_data()

    pending_rows = file_manager.get_pending_rows()

    if pending_rows.empty:
        print("No pending rows to process.")
        file_manager.update_input_json("scrap_json_finished", "True")
        return

    print(f"Pending rows: {len(pending_rows)}")

    for index, row in pending_rows.iterrows():
        question_text = row["Pregunta"]
        url = row["URL"]

        print(f"Processing {question_text} - {url}")

        try:
            soup = load_page(browser, url)
            data = scrape_page(soup)
            file_manager.json_data.append(data)

            file_manager.save_json()
            file_manager.update_row(index, "Scraping", True)
            file_manager.save_csv()

            file_manager.update_input_json("scrap_json_finished", "True")

            time.sleep(random.uniform(3, 6))

        except Exception as e:
            print(f"Error processing {question_text}: {str(e)}")
            continue


def validate_and_create_files(file_manager):
    """
    Validates the existence of required files and creates them if necessary.

    Args:
        file_manager (FileManager): Instance of FileManager to handle file validations.

    Returns:
        None
    """
    file_manager.validate_files()