# Exam Scraper

## Overview

This project is a web scraper designed to automate the retrieval of exam-related questions, discussions, and metadata from online resources. It uses Selenium to interact with web pages and BeautifulSoup for parsing HTML content. The retrieved data is saved in structured formats such as JSON and CSV.

## Features

- **Dynamic Web Scraping**: Supports Google and Bing for searching questions.
- **Data Storage**: Saves progress in CSV and detailed question information in JSON.
- **Customizable**: User requirements are read from a JSON configuration file.
- **Headless Browser**: Can be run in headless mode by modifying the browser setup.

## Requirements

- Python 3.7+
- Google Chrome and compatible ChromeDriver
- Required Python libraries:
  - `selenium`
  - `beautifulsoup4`
  - `pandas`
  - `lxml`

## Setup

### 1. Install Dependencies

Install the required Python libraries:

```bash
pip install selenium beautifulsoup4 pandas lxml
```

### 2. Download ChromeDriver

Ensure you have ChromeDriver installed and compatible with your version of Google Chrome. Place the ChromeDriver executable in the `driver/` directory or adjust the path in the `setup_browser` function.

### 3. Prepare Configuration

Set the `user_requirement.json` file in the `./input/` directory with the following structure:

```json
{
    "exam": "Add Exam Name",
    "exam_main_url": "https://www.examtopics.com/exams/(Add the main url of the exam you want)",
    "max_question": ,
    "extract_csv_finished": "False",
    "scrap_json_finished": "False"
}
```

- `exam`: Name of the exam.
- `exam_main_url`: URL of the main exam page.
- `extract_csv_finished`: set to "False"
- - `scrap_json_finished`: set to "False"

### 4. Run the Script

Execute the script using Python:

```bash
python exam_scraper.py
```

## Output

The script generates the following outputs:

1. **JSON File**: Contains detailed information about each question.
   - Location: `./<exam_name>_output_questions/questions_answer.json`
2. **CSV File**: Tracks scraping progress with question numbers and URLs.
   - Location: `./<exam_name>_output_questions/discussion_url.csv`

## Functionalities

### 1. Browser Setup

The `setup_browser` function initializes a Selenium WebDriver with various configurations for optimal performance.

### 2. Fetching Maximum Questions

The `get_max_questions` function retrieves the maximum number of questions from the user configuration or the exam webpage.

### 3. Searching for Questions

- `search_question_google`: Searches Google for a question and extracts a relevant URL.
- `search_question_bing`: Searches Bing as a fallback when Google fails.

### 4. Scraping Question Data

The `scrape_page` function parses the HTML content of a question page to extract details such as:
- Question text
- Available choices
- Correct answers
- Images associated with the question and answers

### 5. File Management

The `validate_and_create_files` function ensures that all necessary files and directories are created before the script runs.

## Customization

### Adjust Headless Mode

To enable headless mode, uncomment the `options.add_argument("--headless")` line in the `setup_browser` function.

### Modify Search Behavior

To tweak the search query or results filtering, update the `search_question_google` and `search_question_bing` functions.

## Troubleshooting

### Common Issues

1. **ChromeDriver Version Mismatch**:
   Ensure that the ChromeDriver version matches your installed Google Chrome version.

2. **Blocked Requests**:
   Google may block automated requests. If this happens, reduce the scraping speed or rely more on Bing.

3. **Missing Elements**:
   If the webpage structure changes, update the HTML element selectors in the scraping functions.

### Run Exam Demo

Using VisualStudio Code, run "home" using "Open live Server" extension


## License

This project is open-source and available under the MIT License.

---

Feel free to contribute or report issues to improve this project!

