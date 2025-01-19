# Copyright (c) 2025 Diego Martins
# Licensed under the MIT License. See LICENSE file in the project root for details.

import os
import json
from FileManager import FileManager
from BrowserSetup import setup_browser
from URLExtractor import get_max_questions, extract_urls
from QuestionScraper import scrape_question_info

def main():
    user_input_folder = "./input"
    user_requirement_file = os.path.join(user_input_folder, "user_requirement.json")

    # Load user requirements
    with open(user_requirement_file, 'r') as file:
        user_data = json.load(file)
        exam_name = user_data.get("exam", "default_exam")

    # Define output paths
    output_folder = f"./{exam_name}_output_questions"
    json_output_file = os.path.join(output_folder, "questions_answer.json")
    csv_file = os.path.join(output_folder, "discussion_url.csv")

    # Initialize FileManager
    file_manager = FileManager(csv_file=csv_file, json_file=json_output_file, input_json_file=user_requirement_file)
    file_manager.validate_files()

    browser = setup_browser()

    try:

        max_questions = get_max_questions(browser, file_manager)

        extract_urls(browser, file_manager, max_questions)

        scrape_question_info(browser, file_manager)

    finally:
        browser.quit()
        print(f"Process completed. Data saved in {json_output_file}")

if __name__ == "__main__":
    main()
