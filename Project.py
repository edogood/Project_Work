import EpisodeManager  
import IniManager      

# Request the .ini filename
filename = input("Inserire file -ini: ")

# Create an instance of IniManager to parse the .ini file
ini_manager = IniManager.IniManager(filename)

# Get directory and connection string from the IniManager instance
directory = ini_manager.get_directory()
connection_str = ini_manager.get_server()

# Create an instance of EpisodeManager with the parsed data
episode_manager = EpisodeManager.EpisodeManager(directory, connection_str)

# Load episodes data from JSON (if the file exists) or process new .txt files
json_filename = "episodes_data.json"
episodes_data = episode_manager.load_from_json(json_filename)

if not episodes_data:  # If no data is loaded, populate from files
    files = episode_manager.find_files()
    episodes_data = episode_manager.populate_dictionary(files)
    # Save the newly populated data to JSON
    episode_manager.save_to_json(episodes_data, json_filename)

# Insert episode data into the database
episode_ids = episode_manager.insert_episode_into_db(episodes_data)

# Insert characters and lines into the database, passing episode IDs
episode_manager.insert_characters_into_db(episodes_data, episode_ids)
