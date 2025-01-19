# Copyright (c) 2025 Diego Martins
# Licensed under the MIT License. See LICENSE file in the project root for details.

import random
import time
import pandas as pd
from FileManager import FileManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


def fetch_max_questions(browser, exam_url):
    """
    Fetches the maximum number of questions from the exam webpage.

    Args:
        browser (WebDriver): Selenium WebDriver instance.
        exam_url (str): URL of the exam page.

    Returns:
        int: Maximum number of questions found.

    Raises:
        RuntimeError: If the maximum number of questions cannot be fetched.
    """
    browser.get(exam_url)
    time.sleep(3)

    try:
        element = browser.find_element(By.CLASS_NAME, "exam-stat-wrapper-item")
        max_questions = element.find_element(By.TAG_NAME, "span").text.strip()
        return int(max_questions)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch maximum questions: {e}")


def get_max_questions(browser, file_manager):
    """
    Retrieves the maximum number of questions from the JSON configuration or webpage.

    Args:
        browser (WebDriver): Selenium WebDriver instance.
        file_manager (FileManager): FileManager instance to handle JSON files.

    Returns:
        int: Maximum number of questions.
    """
    user_requirements = file_manager.get_input_json_data()
    max_question = user_requirements.get("max_question")
    exam_url = user_requirements["exam_main_url"]

    if max_question:
        print(f"Maximum questions loaded from JSON: {max_question}")
        return int(max_question)

    max_question = fetch_max_questions(browser, exam_url)
    file_manager.update_input_json("max_question", max_question)
    print(f"Maximum questions fetched from webpage: {max_question}")
    return max_question


def search_question(browser, query, search_url, target_domain="examtopics.com", popup_xpath=None):
    """
    Generic function to perform a search and retrieve the first relevant URL.

    Args:
        browser (WebDriver): Selenium WebDriver instance.
        query (str): Search query.
        search_url (str): URL of the search engine.
        target_domain (str): Domain to filter results (default: "examtopics.com").
        popup_xpath (str): XPath of popup element to handle (default: None).

    Returns:
        str or None: Relevant URL if found, otherwise None.
    """
    browser.get(search_url)

    if popup_xpath:
        handle_popup(browser, popup_xpath)

    try:
        search_box = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.submit()
        time.sleep(random.uniform(2, 7))

        if "detected unusual traffic" in browser.page_source.lower():
            print(f"Unusual traffic detected on {search_url}. Aborting search.")
            return None

        links = browser.find_elements(By.XPATH, '//a[@href]')
        for link in links:
            href = link.get_attribute("href")
            if target_domain in href:
                print(f"Found relevant URL on {search_url}: {href}")
                return href

    except Exception as e:
        print(f"Error during search on {search_url}: {e}")

    return None


def handle_popup(browser, popup_xpath):
    """
    Handles popup by clicking the specified element if present.

    Args:
        browser (WebDriver): Selenium WebDriver instance.
        popup_xpath (str): XPath of the popup element to click.

    Returns:
        None
    """
    try:
        consent_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.XPATH, popup_xpath))
        )
        ActionChains(browser).move_to_element(consent_button).click().perform()
        print("Popup handled successfully.")
    except Exception as e:
        print("No popup found or it was already handled.")


def search_question_google(browser, query, target_domain="examtopics.com"):
    """
    Wrapper for performing a search on Google.

    Args:
        browser (WebDriver): Selenium WebDriver instance.
        query (str): Search query.
        target_domain (str): Domain to filter the results.

    Returns:
        str or None: Relevant URL if found, otherwise None.
    """
    return search_question(
        browser,
        query,
        search_url="https://www.google.com",
        target_domain=target_domain,
        popup_xpath='//button[@id="L2AGLb"]'
    )


def search_question_bing(browser, query, target_domain="examtopics.com"):
    """
    Wrapper for performing a search on Bing.

    Args:
        browser (WebDriver): Selenium WebDriver instance.
        query (str): Search query.
        target_domain (str): Domain to filter the results.

    Returns:
        str or None: Relevant URL if found, otherwise None.
    """
    return search_question(
        browser,
        query,
        search_url="https://www.bing.com",
        target_domain=target_domain
    )


def extract_urls(browser, file_manager, max_questions, recursion_depth=0, max_recursion=3):
    """
    Extracts URLs for exam questions and saves progress to a CSV file. Uses recursion to handle missing questions.

    Args:
        browser (WebDriver): Selenium WebDriver instance.
        file_manager (FileManager): FileManager instance for handling CSV and JSON files.
        max_questions (int): Total number of questions to extract URLs for.
        recursion_depth (int): Current recursion depth to avoid infinite loops (default: 0).
        max_recursion (int): Maximum allowed recursion depth (default: 3).

    Returns:
        None
    """
    if recursion_depth > max_recursion:
        print("Maximum recursion depth reached. Stopping URL extraction.")
        return

    user_requirements = file_manager.get_input_json_data()
    exam = user_requirements["exam"]
    start_question, progress_data = file_manager.load_csv_progress()

    if user_requirements.get("extract_csv_finished", "False") == "True":
        print("URL extraction already completed.")
        return

    search_engines = [
        {"name": "Google", "function": search_question_google},
        {"name": "Bing", "function": search_question_bing}
    ]

    try:
        print("Starting URL extraction.")
        for question_number in range(start_question + 1, max_questions + 1):
            query = f'ExamTopics exam {exam} topic 1 "question {question_number}" discussion'
            print(f"Searching: {query}")

            found = False
            original_engines = list(search_engines)

            for engine in original_engines:
                url = engine["function"](browser, query)

                if url:
                    file_manager.append_csv_row([f"Question #: {question_number}", url, False])
                    print(f"Question {question_number}: URL found using {engine['name']}.")
                    found = True
                    break
                else:
                    search_engines.append(search_engines.pop(search_engines.index(engine)))
                    print(f"{engine['name']} did not find results and has been deprioritized.")

            if not found:
                print(f"Question {question_number}: No URL found on any search engine.")

        missing_questions = verify_missing_questions(file_manager.csv_data, max_questions)
        if missing_questions:
            print(f"Retrying missing questions: {missing_questions}.")
            for question_number in missing_questions:
                query = f"exam {exam} topic 1 question {question_number} discussion"
                for engine in search_engines:
                    url = engine["function"](browser, query)
                    if url:
                        file_manager.append_csv_row([f"Question #: {question_number}", url, False])
                        print(f"Retry Question {question_number}: URL found using {engine['name']}.")
                        break
                else:
                    print(f"Retry Question {question_number}: No URL found on any search engine.")

        file_manager.update_input_json("extract_csv_finished", "True")
        print("URL extraction completed and status updated in JSON.")

    except Exception as e:
        print(f"General error during URL extraction: {e}")


def verify_missing_questions(progress_data, max_questions):
    """
    Verifies which questions are missing from the progress data.

    Args:
        progress_data (DataFrame): Progress data containing scraped questions.
        max_questions (int): Total number of questions.

    Returns:
        list: List of missing question numbers.
    """
    found_questions = progress_data["Pregunta"].apply(lambda x: int(x.split("#: ")[1])).tolist()
    all_questions = set(range(1, max_questions + 1))
    missing_questions = list(all_questions - set(found_questions))
    return missing_questions