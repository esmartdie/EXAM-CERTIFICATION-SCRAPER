import os
import pandas as pd
import json

class FileManager:
    """
    Handles operations related to CSV and JSON files, including loading, saving,
    and managing progress for question scraping.

    Attributes:
        csv_file (str): Path to the CSV file.
        json_file (str): Path to the output JSON file.
        input_json_file (str): Path to the input JSON file (user requirements).
        csv_data (DataFrame): Data loaded from the CSV file.
        json_data (list): Data loaded from the output JSON file.
        input_json_data (dict): Data loaded from the input JSON file.
    """
    def __init__(self, csv_file, json_file, input_json_file):
        self.csv_file = csv_file
        self.json_file = json_file
        self.input_json_file = input_json_file
        self.csv_data = self._load_csv()
        self.json_data = self._load_json(self.json_file)
        self.input_json_data = self._load_json(self.input_json_file)

    def _load_csv(self):
        if os.path.exists(self.csv_file):
            return pd.read_csv(self.csv_file)
        return pd.DataFrame(columns=["Pregunta", "URL", "Scraping"])

    def load_csv_progress(self):
        data = pd.read_csv(self.csv_file)
        if not data.empty:
            last_question = data['Pregunta'].iloc[-1].split("#: ")[1]
            return int(last_question), data
        return 0, pd.DataFrame(columns=["Pregunta", "URL", "Scraping"])

    def save_csv(self):
        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)
        self.csv_data.to_csv(self.csv_file, index=False)

    def _load_json(self, filepath):
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {} if filepath == self.input_json_file else []

    def save_json(self):
        os.makedirs(os.path.dirname(self.json_file), exist_ok=True)
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.json_data, f, ensure_ascii=False, indent=4)

    def validate_files(self):
        if not os.path.exists(self.csv_file):
            self.save_csv()
        if not os.path.exists(self.json_file):
            self.json_data = []
            self.save_json()
        if not os.path.exists(self.input_json_file):
            raise FileNotFoundError(f"Input JSON file not found: {self.input_json_file}")

    def get_pending_rows(self):
        if "Scraping" not in self.csv_data.columns:
            self.csv_data["Scraping"] = False
        return self.csv_data[~self.csv_data["Scraping"]].copy()

    def append_csv_row(self, row):
        self.csv_data = pd.concat([
            self.csv_data,
            pd.DataFrame([row], columns=["Pregunta", "URL", "Scraping"])
        ]).reset_index(drop=True)
        self.save_csv()

    def update_row(self, index, column, value):
        self.csv_data.loc[index, column] = value
        self.save_csv()

    def get_input_json_data(self):
        """
        Returns the data from the input JSON file.

        Returns:
            dict: Data loaded from the input JSON file.
        """
        return self.input_json_data

    def update_input_json(self, key, value):
        """
        Updates a specific key in the input JSON data and saves the changes.

        Args:
            key (str): Key to update in the input JSON.
            value: New value for the specified key.
        """
        self.input_json_data[key] = value
        with open(self.input_json_file, "w", encoding="utf-8") as f:
            json.dump(self.input_json_data, f, ensure_ascii=False, indent=4)