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
                # Open the .txt file and read line by line
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.readlines()
                    for line in content:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            character_name = parts[0].strip()  # Character name before the colon
                            line_content = parts[1].strip()  # Dialogue content after the colon
                            found = False
                            
                            # Search if the character already exists in the script list
                            for entry in episode_dict["script"]:
                                if entry["nome personaggio"] == character_name:
                                    entry["battute"].append(line_content)  # Add the dialogue line
                                    found = True
                                    break
                            
                            # If character not found, create a new entry for them
                            if not found:
                                episode_dict["script"].append({
                                    "nome personaggio": character_name,
                                    "battute": [line_content]
                                })
                    episodes_data.append(episode_dict)
            except Exception as e:
                print(f"Error processing file {f}: {str(e)}")
            finally:
                # Cleanup or closing file resources if needed (Python handles this with 'with' automatically)
                pass
        return episodes_data

    def insert_episode_into_db(self, episodes_data: list):
        """
        Inserts the episode data into the database.

        Args:
            episodes_data (list): A list of episode dictionaries containing episode information.

        Returns:
            list: A list of episode IDs inserted into the database.
        """
        episode_ids = []
        conn = None
        cursor = None
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()

            for episode in episodes_data:
                episode_name = episode["episode_number"]  # Full episode name (e.g., "voy_e_1")

                # Ensure episode_name is a string
                if isinstance(episode_name, int):
                    episode_name = str(episode_name)

                # Split the name to extract episode number (e.g., "1" from "voy_e_1")
                episode_number = episode_name.split("_e_")[1]
                season = self.determine_season_from_filename(episode_name, self.prefix_map)  # Get season from prefix

                cursor.execute("""EXEC dbo.InsertEpisode ?, ?""", (episode_number, season))
                
                # Fetch the episode ID after insertion
                episode_id = cursor.fetchval()
                if not episode_id:
                    print(f"Error inserting episode {episode_number}, season {season}.")
                    continue

                episode_ids.append(episode_id)

            conn.commit()
            print("Episodes successfully inserted.")
            return episode_ids

        except Exception as e:
            print(f"Error inserting episode into the database: {str(e)}")
            return None
        
        finally:
            # Ensure resources are cleaned up
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def insert_characters_into_db(self, episodes_data: list, episode_ids: list):
        """
        Inserts character data (lines) into the database for each episode.

        Args:
            episodes_data (list): A list of episode dictionaries containing character data.
            episode_ids (list): A list of episode IDs corresponding to the episodes.

        Returns:
            None
        """
        conn = None
        cursor = None
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            
            for i, episode in enumerate(episodes_data):
                episode_id = episode_ids[i]
                characters_lines = episode.get("script", [])  # Use .get() to avoid errors if "script" is missing

                if not characters_lines:
                    print(f"No script data found for episode {episode['episode_number']}")
                    continue  # Skip if no script data is found for this episode

                # Insert each character's lines into the database
                for entry in characters_lines:
                    character = entry["nome personaggio"]
                    for line in entry["battute"]:
                        cursor.execute("""EXEC dbo.InsertCharacterLines ?, ?, ?""",
                                        (character, episode_id, line))
            conn.commit()
            print("Characters and lines successfully inserted.")
        
        except Exception as e:
            print(f"Error inserting characters into the database: {str(e)}")
            conn.rollback()

        finally:
            # Ensure resources are cleaned up
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def save_to_json(self, episodes_data: list, json_filename: str):
        """
        Saves the episode data into a JSON file.

        Args:
            episodes_data (list): The episode data to be saved.
            json_filename (str): The path where the JSON file will be saved.

        Returns:
            None
        """
        try:
            with open(json_filename, "w", encoding="utf-8") as json_file:
                json.dump(episodes_data, json_file, ensure_ascii=False, indent=4)
            print(f"Episode data successfully saved to {json_filename}")
        except Exception as e:
            print(f"Error saving data to JSON file: {str(e)}")
        finally:
            # File handles are automatically managed, so no need for additional cleanup
            pass

    def load_from_json(self, json_filename: str) -> list:
        """
        Loads episode data from a JSON file.

        Args:
            json_filename (str): The path to the JSON file to load.

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
        finally:
            # File handles are automatically managed, so no need for additional cleanup
            pass
