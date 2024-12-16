import os
import json
import pyodbc

class EpisodeManager:
    def __init__(self, directory: str, connection_str: str):
        """
        Initializes the EpisodeManager class with the directory containing the episode .txt files
        and the database connection string for SQL Server.
        
        Args:
            directory (str): Path to the directory where episode .txt files are stored.
            connection_str (str): Connection string to connect to the SQL Server database.
        """
        self.directory = directory  # Store the directory to search for .txt files
        self.conn_str = connection_str  # Store the connection string to connect to the database
        
    def find_files(self) -> list:
        """
        Finds all the .txt files in the specified directory.

        Returns:
            list: A list of filenames that end with ".txt" in the specified directory.
        """
        # List all files in the directory and filter only those with a .txt extension
        onlyfiles = [f for f in os.listdir(self.directory)
                     if os.path.isfile(os.path.join(self.directory, f)) and f.endswith(".txt")]
        return onlyfiles

    def determine_season(self, episode_name: str, prefix_map: dict) -> int:
        """
        Determines the season number based on the episode name prefix, using the prefix map for series.

        Args:
            episode_name (str): The episode filename (without extension) to extract the season from.
            prefix_map (dict): A dictionary mapping series prefixes to season numbers.

        Returns:
            int: The season number (1-6) if the prefix is valid, otherwise returns 0 if not found.
        """
        # Loop through the prefix_map and match the episode name prefix to determine the season
        for prefix, season in prefix_map.items():
            if episode_name.startswith(prefix):
                return season
        return 0  # Return 0 if no valid prefix is found (season is undefined)

    # Prefix map for different Star Trek series and their respective season numbers
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
        Populates a list of dictionaries with episode data parsed from .txt files.

        Args:
            files (list): A list of .txt filenames to process and extract episode data from.

        Returns:
            list: A list of dictionaries, each containing episode number and script (character lines).
        """
        episodes_data = []  # Initialize an empty list to hold the episode data
        
        # Loop through each file in the provided list of .txt filenames
        for f in files:
            # Initialize an empty dictionary for each episode
            episode_dict = {"episode_number": "", "script": []}  # Removed 'characters_data' and 'prefix' from JSON
            # Extract episode name by removing the '.txt' extension
            episode_name = f[:-4] if f.endswith(".txt") else f
            # Check if the filename follows the expected format with "_e_"
            if "_e_" in episode_name:
                try:
                    prefix, episode = episode_name.split("_e_")  # Split the filename to get episode number
                    episode_dict["episode_number"] = int(episode)  # Assign the episode number to the dictionary
                except ValueError:
                    print(f"Incorrect format for file {f}. Ignored.")  # Handle incorrect format error
                    continue  # Skip this file and continue with the next one
            else:
                print(f"Incorrect format for file {f}. Ignored.")  # Handle files not following expected naming format
                continue  # Skip this file and continue with the next one
            
            # Build the full path to the file
            file_path = os.path.join(self.directory, f)
            try:
                # Open the file and read its content line by line
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.readlines()  # Read all lines from the file
                    # Loop through each line in the file to extract character names and their lines
                    for line in content:
                        parts = line.split(":", 1)  # Split each line by the first occurrence of ":"
                        if len(parts) == 2:  # Ensure the line contains both character name and line
                            character_name = parts[0].strip()  # Extract the character's name
                            line_content = parts[1].strip()  # Extract the actual line content

                            # Search for the character in the existing script data
                            found = False
                            for entry in episode_dict["script"]:
                                if entry["nome personaggio"] == character_name:
                                    entry["battute"].append(line_content)  # Add the line to the existing character's lines
                                    found = True
                                    break
                            
                            if not found:
                                # If the character is not found, create a new entry for this character
                                episode_dict["script"].append({
                                    "nome personaggio": character_name,
                                    "battute": [line_content]  # Add the first line for this character
                                })
                    # After processing the file, add the episode data to the episodes list
                    episodes_data.append(episode_dict)
            except Exception as e:
                print(f"Error processing file {f}: {str(e)}")  # Handle errors during file reading and processing

        # Return the list of populated episode data
        return episodes_data

    def insert_episode_into_db(self, episodes_data: list):
        """
        Inserts episode data (episode number and season) into the database.

        Args:
            episodes_data (list): A list of dictionaries containing episode data.

        Returns:
            list: A list of episode IDs inserted successfully into the database.
        """
        episode_ids = []  # List to store the IDs of successfully inserted episodes
        try:
            # Connect to the SQL Server database
            conn = pyodbc.connect(self.conn_str)  
            cursor = conn.cursor()

            # Loop through each episode's data to insert into the database
            for episode in episodes_data:
                episode_number = episode["episode_number"]  # Get the episode number from the dictionary

                # Determine the season based on the episode number (we no longer use the prefix for season)
                episode_name = f"{episode_number}"  # Use the episode number directly for determining season
                season = self.determine_season(episode_name, self.prefix_map)  # Get season using the prefix map

                # Execute the database query to insert the episode into the database
                cursor.execute("""EXEC dbo.InsertEpisode ?, ?""", (episode_number, season))

                # Retrieve the episode ID after insertion
                episode_id = cursor.fetchval()
                if not episode_id:
                    print(f"Error inserting episode {episode_number}, season {season}.")
                    continue  # If insertion fails, skip to the next episode

                # Append the episode ID to the list
                episode_ids.append(episode_id)

            conn.commit()  # Commit the transaction to the database
            cursor.close()  # Close the cursor
            conn.close()  # Close the connection
            print("Episodes successfully inserted.")
            return episode_ids  # Return the list of inserted episode IDs

        except Exception as e:
            print(f"Error inserting episode into the database: {str(e)}")
            return None  # Return None if there was an error

    def insert_characters_into_db(self, episodes_data: list, episode_ids: list):
        """
        Inserts character names and their lines into the database.

        Args:
            episodes_data (list): A list of dictionaries containing episode data.
            episode_ids (list): A list of episode IDs corresponding to the inserted episodes in the database.
        """
        try:
            # Connect to the SQL Server database
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()

            # Loop through each episode's data
            for i, episode in enumerate(episodes_data):
                episode_id = episode_ids[i]  # Get the corresponding episode ID for this episode
                characters_lines = episode["script"]  # Get the characters and their lines from the episode data
                
                # Loop through each character's lines
                for entry in characters_lines:
                    character = entry["nome personaggio"]  # Extract the character's name
                    for line in entry["battute"]:
                        # Insert each character and their line into the database
                        cursor.execute("""EXEC dbo.InsertCharacterLines ?, ?, ?""",
                                        (character, episode_id, line))

            conn.commit()  # Commit the transaction to the database
            cursor.close()  # Close the cursor
            conn.close()  # Close the connection
            print("Characters and lines successfully inserted.")
        except Exception as e:
            print(f"Error inserting characters into the database: {str(e)}")
            conn.rollback()  # Rollback transaction in case of error

    def save_to_json(self, episodes_data: list, json_filename: str):
        """
        Saves the episode data to a JSON file.

        Args:
            episodes_data (list): A list of dictionaries containing episode data.
            json_filename (str): The path to the JSON file where the data should be saved.
        """
        try:
            # Open the specified JSON file and write the episode data to it
            with open(json_filename, "w", encoding="utf-8") as json_file:
                json.dump(episodes_data, json_file, ensure_ascii=False, indent=4)
            print(f"Episode data successfully saved to {json_filename}")
        except Exception as e:
            print(f"Error saving data to JSON file: {str(e)}")  # Handle errors when saving to JSON file
    
    def load_from_json(self, json_filename: str) -> list:
        """
        Loads episode data from a JSON file.

        Args:
            json_filename (str): The path to the JSON file to load the data from.

        Returns:
            list: A list of dictionaries containing episode data.
        """
        try:
            # Open the specified JSON file and read the data into a list
            with open(json_filename, "r", encoding="utf-8") as json_file:
                episodes_data = json.load(json_file)
            print(f"Episode data successfully loaded from {json_filename}")
            return episodes_data
        except Exception as e:
            print(f"Error loading data from JSON file: {str(e)}")
            return []  # Return an empty list if there is an error loading the data
