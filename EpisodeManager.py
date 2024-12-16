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

    def determine_season(self, episode_name: str, prefix_map: dict) -> int:
        """
        Determines the season based on the prefix in the filename, using a map of prefixes for different series.
 
        Args:
            episode_name (str): The name of the episode file (without the .txt extension).
            prefix_map (dict): A dictionary mapping series prefixes (e.g., "VOY", "ENT", etc.) to season numbers.
 
        Returns:
            int: The season number (1-6) if the prefix is valid, otherwise 0.
        """
        for prefix, season in prefix_map.items():
            if episode_name.startswith(prefix):
                return season
        return 0  # If prefix is not valid, returns 0 (season not defined)

    # Example prefix map for series
    prefix_map = {
        "VOY": 1,  # Voyager (Season 1)
        "ENT": 2,  # Enterprise (Season 2)
        "TNG": 3,  # The Next Generation (Season 3)
        "DS9": 4,  # Deep Space Nine (Season 4)
        "TOS": 5,  # The Original Series (Season 5)
        "TAS": 6,  # The Animated Series (Season 6)
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
            episode_dict = {"episode_number": "", "script": []}  # Removed characters_data and prefix
            # Extract the episode name (without the '.txt' suffix)
            episode_name = f[:-4] if f.endswith(".txt") else f
            # New format: "VOY_1_e_98.txt" -> extract episode number
            if "_e_" in episode_name:
                try:
                    prefix, episode = episode_name.split("_e_")
                    episode_dict["episode_number"] = int(episode)  # Set the episode number
                except ValueError:
                    print(f"Incorrect format for file {f}. Ignored.")  # Handle format errors
                    continue
            else:
                print(f"Incorrect format for file {f}. Ignored.")  # Message for files that don't follow the expected format
                continue
            # Full file path
            file_path = os.path.join(self.directory, f)
            try:
                # Open and read the file content
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.readlines()  # Read the content line by line
                    # Process each line
                    for line in content:
                        # Split the line at the first colon ":"
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            character_name = parts[0].strip()  # Extract character's name
                            line_content = parts[1].strip()  # Extract the line
                            # Check if the character already exists in the script list
                            found = False
                            for entry in episode_dict["script"]:
                                if entry["nome personaggio"] == character_name:
                                    entry["battute"].append(line_content)  # Add the line to the existing character
                                    found = True
                                    break
                            if not found:
                                # If character doesn't exist, create a new entry for them
                                episode_dict["script"].append({
                                    "nome personaggio": character_name,
                                    "battute": [line_content]  # Add the first line for this character
                                })
                    # Add the episode to the list
                    episodes_data.append(episode_dict)
            except Exception as e:
                print(f"Error processing file {f}: {str(e)}")  # Debug
        # Return the data (a list of dictionaries)
        return episodes_data

    def insert_episode_into_db(self, episodes_data: list):
        episode_ids = []  # List to store the IDs of inserted episodes
        try:
            conn = pyodbc.connect(self.conn_str)  # Connessione al database
            cursor = conn.cursor()

            for episode in episodes_data:
                episode_number = episode["episode_number"]

                # Determina la stagione in base al nome dell'episodio
                episode_name = f"{episode_number}"  # Non utilizziamo più il prefisso
                season = self.determine_season(episode_name, self.prefix_map)  # Ottieni la stagione dalla logica di determinazione

                # Inserisci l'episodio nel database
                cursor.execute("""EXEC dbo.InsertEpisode ?, ?""", (episode_number, season))
                
                # Recupera l'ID dell'episodio appena inserito
                episode_id = cursor.fetchval()
                if not episode_id:
                    print(f"Error inserting episode {episode_number}, season {season}.")
                    continue  # Se l'inserimento fallisce, salta al prossimo episodio

                # Aggiungi l'ID dell'episodio alla lista
                episode_ids.append(episode_id)

            conn.commit()  # Conferma la transazione
            cursor.close()  # Chiudi il cursore
            conn.close()  # Chiudi la connessione
            print("Episodes successfully inserted.")
            return episode_ids  # Restituisci gli ID degli episodi inseriti correttamente

        except Exception as e:
            print(f"Error inserting episode into the database: {str(e)}")
            return None  # Restituisci None in caso di errore

    def insert_characters_into_db(self, episodes_data: list, episode_ids: list):
        """
        Inserts characters and their lines into the 'characters' table in the database.
 
        Args:
            episodes_data (list): A list of dictionaries containing episode data.
            episode_ids (list): A list of episode IDs that were inserted into the database.
        """
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            for i, episode in enumerate(episodes_data):
                # Associate the episode ID
                episode_id = episode_ids[i]  # Use the corresponding ID from the episode IDs list
                # Get the characters and their lines
                characters_lines = episode["script"]
                for entry in characters_lines:
                    character = entry["nome personaggio"]
                    for line in entry["battute"]:
                        # Insert each character and their line into the database
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
        """
        Saves the episode data to a JSON file.

        Args:
            episodes_data (list): A list of dictionaries containing episode data.
            json_filename (str): The path where the JSON file will be saved.
        """
        try:
            with open(json_filename, "w", encoding="utf-8") as json_file:
                json.dump(episodes_data, json_file, ensure_ascii=False, indent=4)
            print(f"Episode data successfully saved to {json_filename}")
        except Exception as e:
            print(f"Error saving data to JSON file: {str(e)}")
    
    def load_from_json(self, json_filename: str) -> list:
        """
        Loads the episode data from a JSON file.

        Args:
            json_filename (str): The path of the JSON file to load.

        Returns:
            list: A list of dictionaries containing episode data.
        """
        try:
            with open(json_filename, "r", encoding="utf-8") as json_file:
                episodes_data = json.load(json_file)
            print(f"Episode data successfully loaded from {json_filename}")
            return episodes_data
        except Exception as e:
            print(f"Error loading data from JSON file: {str(e)}")
            return []
