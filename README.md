This repository contains a Python project that implements an EpisodeManager class, which manages episodes, handles backup operations, and processes configurations using JSON and INI files.

The project is structured to include the following key components:

EpisodeManager Class: A class that manages episodes by creating and reading a JSON file.
InImage Class: A class that finds an image file associated with a given episode, based on a file path.
Backup File (Bak): A backup of the server data, typically stored as a .bak file.
Project.py: The main executable script that ties everything together by executing the classes and operations.
config.ini: A configuration file used for setting up parameters, such as connection strings and paths.

Star_Trek_Project
├── EpisodeManager.py          # Main class for managing episodes and JSON data
├── InImage.py                 # Class for finding images related to episodes
├── Project.py                 # Main entry point that executes the classes
├── data/
│   └── episodes.json          # JSON file storing episode details
├── backups/
│   └── server.bak             # Backup file for the server data
├── config.ini                 # Configuration file for connection string, paths, etc.
└── README.md                  # This README file
