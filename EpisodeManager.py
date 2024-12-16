import os
import json
import pyodbc

class EpisodeManager:
    def __init__(self, directory: str, connection_str: str):
        """
        Initializes the class with the directory containing .txt files and the database connection string.

        Args:
            directory (str): The path to the directory containing the .txt files of episodes.
            connection_str (str): The database connection string for SQL Server.
        """
        self.directory = directory  # Directory to search for .txt files
        self.conn_str = connection_str  # Database connection string
        
    def find_files(self) -> list:
        """
        Finds all .txt files in the specified directory.

        Returns:
            list: A list of .txt filenames found in the directory.
        """
        onlyfiles = [f for f in os.listdir(self.directory)
                     if os.path.isfile(os.path.join(self.directory, f)) and f.endswith(".txt")]
        return onlyfiles

    def determine_season_from_filename(self, episode_name: str, prefix_map: dict) -> int:
        """
        Determines the season based on the prefix in the filename, using a map of prefixes for different series.

        Args:
            episode_name (str): The name of the episode file (without the .txt extension).
            prefix_map (dict): A dictionary mapping series prefixes (e.g., "VOY", "ENT", etc.) to season numbers.

        Returns:
            int: The season number (1-6) if the prefix is valid, otherwise 0 (unknown season).
        """
        for prefix, season in prefix_map.items():
            if episode_name.lower().startswith(prefix.lower()):
                return season
        return 0  # If prefix is not valid, return 0 (season not defined)

    # Example prefix map for series
    prefix_map = {
        "voy": 1,  # Voyager (Season 1)
        "ent": 2,  # Enterprise (Season 2)
        "tng": 3,  # The Next Generation (Season 3)
        "ds9": 4,  # Deep Space Nine (Season 4)
        "tos": 5,  # The Original Series (Season 5)
        "tas": 6,  # The Animated Series (Season 6)
    }

    def populate_dictionary(self, files: list) -> list:
        """
        Populates a dictionary with episode data from .txt files.

        Args:
            files (list): A list of .txt filenames to process.

        Returns:
            list: A list of dictionaries containing episode data, including characters and their lines.
        """
        episodes_data = []
        for f in files:
            episode_dict = {"episode_number": "", "script": []} 
            episode_name = f[:-4]  # Remove ".txt" suffix
            
            # Save the full name as episode_number (e.g., "voy_e_1")
            episode_dict["episode_number"] = episode_name  # Save complete name
            
            file_path = os.path.join(self.directory, f)
            
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.readlines()
                    for line in content:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            character_name = parts[0].strip()
                            line_content = parts[1].strip()
                            found = False
                            for entry in episode_dict["script"]:
                                if entry["nome personaggio"] == character_name:
                                    entry["battute"].append(line_content)
                                    found = True
                                    break
                            if not found:
                                episode_dict["script"].append({
                                    "nome personaggio": character_name,
                                    "battute": [line_content]
                                })
                    episodes_data.append(episode_dict)
            except Exception as e:
                print(f"Error processing file {f}: {str(e)}")
        return episodes_data

    def insert_episode_into_db(self, episodes_data: list):
        episode_ids = []
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()

            for episode in episodes_data:
                episode_name = episode["episode_number"]  # Full episode name (e.g., "voy_e_1")

                # Assicurati che episode_name sia una stringa
                if isinstance(episode_name, int):
                    episode_name = str(episode_name)

                # Ora facciamo lo split, supponendo che episode_name sia una stringa
                episode_number = episode_name.split("_e_")[1]  # Extract episode number (e.g., "1")
                season = self.determine_season_from_filename(episode_name, self.prefix_map)  # Determine season based on prefix

                cursor.execute("""EXEC dbo.InsertEpisode ?, ?""", (episode_number, season))
                
                episode_id = cursor.fetchval()
                if not episode_id:
                    print(f"Error inserting episode {episode_number}, season {season}.")
                    continue

                episode_ids.append(episode_id)

            conn.commit()
            cursor.close()
            conn.close()
            print("Episodes successfully inserted.")
            return episode_ids

        except Exception as e:
            print(f"Error inserting episode into the database: {str(e)}")
            return None

    def insert_characters_into_db(self, episodes_data: list, episode_ids: list):
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            for i, episode in enumerate(episodes_data):
                episode_id = episode_ids[i]
                characters_lines = episode.get("script", [])  # Usare .get() per evitare errori se "script" non esiste

                if not characters_lines:
                    print(f"No script data found for episode {episode['episode_number']}")
                    continue  # Se non c'è script, continua con il prossimo episodio

                for entry in characters_lines:
                    character = entry["nome personaggio"]
                    for line in entry["battute"]:
                        cursor.execute("""EXEC dbo.InsertCharacterLines ?, ?, ?""",
                                        (character, episode_id, line))
            conn.commit()
            cursor.close()
            conn.close()
            print("Characters and lines successfully inserted.")
        except Exception as e:
            print(f"Error inserting characters into the database: {str(e)}")
            conn.rollback()

    def save_to_json(self, episodes_data: list, json_filename: str):
        try:
            with open(json_filename, "w", encoding="utf-8") as json_file:
                json.dump(episodes_data, json_file, ensure_ascii=False, indent=4)
            print(f"Episode data successfully saved to {json_filename}")
        except Exception as e:
            print(f"Error saving data to JSON file: {str(e)}")

    def load_from_json(self, json_filename: str) -> list:
        """
        Loads the episode data from a JSON file, extracting only the episode number by removing the prefix.

        Args:
            json_filename (str): The path of the JSON file to load.

        Returns:
            list: A list of dictionaries containing episode data, with episode number extracted (no prefix).
        """
        try:
            with open(json_filename, "r", encoding="utf-8") as json_file:
                episodes_data = json.load(json_file)
            print(f"Episode data successfully loaded from {json_filename}")
            return episodes_data
        except Exception as e:
            print(f"Error loading data from JSON file: {str(e)}")
            return []
