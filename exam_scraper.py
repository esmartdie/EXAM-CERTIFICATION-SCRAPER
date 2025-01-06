import random
import os
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


def setup_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
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


def load_user_requirements(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_user_requirements(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_max_questions(browser, user_requirement_file):
    user_requirements = load_user_requirements(user_requirement_file)
    exam_url = user_requirements["exam_main_url"]
    max_question = user_requirements["max_question"]
    if not max_question:
        browser.get(exam_url)
        time.sleep(3)
        try:
            element = browser.find_element(By.CLASS_NAME, "exam-stat-wrapper-item")
            max_questions = element.find_element(By.TAG_NAME, "span").text.strip()
            user_requirements["max_question"] = max_questions
            save_user_requirements(user_requirements, user_requirement_file)
            print(f"Máximo número de preguntas encontrado: {max_questions} y guardado en el JSON.")
            return int(max_questions)
        except Exception as e:
            raise Exception(f"Error al obtener el número máximo de preguntas: {str(e)}")
    else:
        print(f"Máximo número de preguntas cargado desde el JSON: {max_question}.")
        return int(max_question)


def search_question(browser, query):
    search_url = "https://www.google.com"
    browser.get(search_url)

    try:
        browser.maximize_window()
        browser.execute_script("document.body.style.zoom='100%'")
        consent_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@id="L2AGLb"]'))
        )
        browser.execute_script("arguments[0].scrollIntoView(true);", consent_button)
        actions = ActionChains(browser)
        actions.move_to_element(consent_button).click().perform()
        print("Ventana emergente manejada con éxito.")
    except Exception as e:
        print("No se encontró ventana emergente o ya fue manejada:")

    search_box = browser.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.submit()
    time.sleep(random.uniform(2, 7))
    try:
        links = browser.find_elements(By.XPATH, '//a[@href]')
        for link in links:
            href = link.get_attribute("href")
            if "https://www.examtopics.com/" in href:
                return href
    except Exception as e:
        print(f"Error al buscar enlaces: {e}")

    return None


def scrap_question_number(soup):
    header_div = soup.find("div", class_="question-discussion-header")
    if not header_div:
        raise Exception("No se encontró la cabecera de la pregunta.")
    inner_div = header_div.find("div")
    if not inner_div:
        raise Exception("No se encontró el div interno con el número de pregunta.")
    return inner_div.get_text(strip=True).split("Topic #:")[0].strip()


def load_page(browser, url, wait_time=10):
    try:
        browser.get(url)
        WebDriverWait(browser, wait_time).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-discussion-header"))
        )
        return BeautifulSoup(browser.page_source, "html.parser")
    except Exception as e:
        raise Exception(f"Error al cargar la página {url}: {str(e)}")


def load_csv_progress(output_file):
    if os.path.exists(output_file):
        data = pd.read_csv(output_file)
        if not data.empty:
            last_question = data['Pregunta'].iloc[-1].split("#: ")[1]
            return int(last_question), data
    return 0, pd.DataFrame(columns=["Pregunta", "URL", "Scraping"])


def save_csv_progress(data, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    data.to_csv(output_file, index=False)


def scrape_page(soup):
    try:
        question_number = scrap_question_number(soup)
        question_body = soup.find("div", class_="question-body mt-3 pt-3 border-top")
        if not question_body:
            raise Exception("No se encontró el cuerpo de la pregunta.")

        # Extract question text
        question_text_element = question_body.find("p", class_="card-text")
        if not question_text_element:
            raise Exception("No se encontró el texto de la pregunta.")
        question_text = question_text_element.get_text(strip=True)

        # Extract question images
        question_image_src = [
            format_image_url(img_tag['src'])
            for img_tag in question_text_element.find_all("img")
        ]

        # Process answer section
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

        # Process choices
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
        raise Exception(f"Error al procesar los datos de la página: {str(e)}")

def format_image_url(img_src):
    """
    Formatea la URL de una imagen dependiendo de su estructura.
    """
    if img_src.startswith("/"):
        return f"https://www.examtopics.com{img_src}"
    elif img_src.startswith("http"):
        return img_src
    else:
        raise ValueError(f"Formato de URL no reconocido: {img_src}")

def log_error(question_text, url, error_message, output_folder="./output_questions"):
    os.makedirs(output_folder, exist_ok=True)
    log_file_path = os.path.join(output_folder, "scraping_errors.log")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{question_text}, {url}, {error_message}\n")


def extract_question_number(question_text):
    try:
        return int(question_text.split("#: ")[1])
    except (IndexError, ValueError):
        raise ValueError(f"No se pudo extraer el número de pregunta de: {question_text}")


def extract_urls(browser, csv_file, max_questions, user_requirement_file):
    user_requirements = load_user_requirements(user_requirement_file)
    exam = user_requirements["exam"]
    start_question, progress_data = load_csv_progress(csv_file)

    if user_requirements["extract_csv_finished"] != "False":
        print("Extracción de URLs ya completada previamente.")
        return

    try:
        print(f"Comenzando desde la pregunta {start_question + 1}.")
        for question_number in range(start_question + 1, max_questions + 1):
            query = f"exam {exam} topic 1 question {question_number} discussion"
            print(f"Buscando: {query}")

            try:
                url = search_question(browser, query)
                if url:
                    progress_data = pd.concat([
                        progress_data,
                        pd.DataFrame([[f"Question #: {question_number}", url, False]], columns=["Pregunta", "URL", "Scraping"])
                    ]).reset_index(drop=True)
                    save_csv_progress(progress_data, csv_file)
                    print(f"Pregunta {question_number}: URL encontrada.")
                else:
                    print(f"Pregunta {question_number}: No se encontró URL.")

                time.sleep(random.uniform(2, 8))

            except Exception as e:
                print(f"Error al procesar la pregunta {question_number}: {str(e)}")
                continue

        if (start_question+1) == max_questions:
            user_requirements["extract_csv_finished"] = "True"
            save_user_requirements(user_requirements, user_requirement_file)
            print("Extracción de URLs completada y estado actualizado en el JSON.")

    except Exception as e:
        print(f"Error general durante la extracción: {str(e)}")


def scrape_question_info(browser, csv_file, json_output_file, user_requirement_file):
    user_requirements = load_user_requirements(user_requirement_file)

    if os.path.exists(json_output_file) and os.path.getsize(json_output_file) > 0:
        with open(json_output_file, "r", encoding="utf-8") as f:
            output_data = json.load(f)
    else:
        output_data = []

    try:
        csv_data = pd.read_csv(csv_file)

        if csv_data["Scraping"].dtype == bool:
            pending_rows = csv_data[~csv_data["Scraping"]].copy()
        else:
            csv_data["Scraping"] = csv_data["Scraping"].astype(str).str.strip()
            pending_rows = csv_data[csv_data["Scraping"] == "False"].copy()

        pending_rows["QuestionNumber"] = pending_rows["Pregunta"].apply(extract_question_number)
        pending_rows = pending_rows.sort_values(by="QuestionNumber")

        if pending_rows.empty:
            print("No hay filas pendientes de procesar.")
            user_requirements["scrap_json_finished"] = "True"
            save_user_requirements(user_requirements, user_requirement_file)
            return

        print(f"Filas pendientes: {len(pending_rows)}")

    except Exception as e:
        print(f"Error al leer el archivo CSV: {str(e)}")
        return

    for index, row in pending_rows.iterrows():
        question_text = row["Pregunta"]
        url = row["URL"]

        print(f"Procesando {question_text} - {url}")

        try:
            soup = load_page(browser, url)
            data = scrape_page(soup)
            output_data.append(data)
            print(f"{question_text} extraída con éxito.")

            with open(json_output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=4)

            csv_data.loc[index, "Scraping"] = "True"
            csv_data.to_csv(csv_file, index=False)

            time.sleep(random.uniform(3, 6))

        except Exception as e:
            print(f"Error al procesar {question_text}: {str(e)}")
            log_error(question_text, url, str(e))
            continue


def validate_and_create_files(output_folder, json_output_file, csv_file):
    os.makedirs(output_folder, exist_ok=True)
    if not os.path.exists(json_output_file):
        print(f"El archivo JSON {json_output_file} no existe. Creándolo...")
        with open(json_output_file, "w", encoding="utf-8") as json_file:
            json.dump([], json_file, ensure_ascii=False, indent=4)
    if not os.path.exists(csv_file):
        print(f"El archivo CSV {csv_file} no existe. Creándolo...")
        initial_csv_data = pd.DataFrame(columns=["Pregunta", "URL", "Scraping"])
        initial_csv_data.to_csv(csv_file, index=False)


def main():
    user_input_folder = "./input"
    user_requirement_file = os.path.join(user_input_folder, "user_requirement.json")

    with open(user_requirement_file, 'r') as file:
        user_data = json.load(file)
        exam_name = user_data.get("exam", "default_exam")

    output_folder = f"./{exam_name}_output_questions"
    json_output_file = os.path.join(output_folder, "questions_answer.json")
    csv_file = os.path.join(output_folder, "discussion_url.csv")
    os.makedirs(output_folder, exist_ok=True)

    validate_and_create_files(output_folder, json_output_file, csv_file)

    browser = setup_browser()

    try:
        max_questions = get_max_questions(browser, user_requirement_file)
        extract_urls(browser, csv_file, max_questions, user_requirement_file)
        scrape_question_info(browser, csv_file, json_output_file, user_requirement_file)
    finally:
        browser.quit()
        print(f"Proceso completo. Datos guardados en {json_output_file}")



if __name__ == "__main__":
    main()
