class IniManager:
    def __init__(self, filename: str):
        """
        Initializes the IniManager by reading the given INI file to extract 
        directory and server information.

        Args:
            filename (str): The path to the INI file to be read.

        Sets:
            self.__directory (str): The directory path read from the INI file.
            self.__server (str): The server connection string read from the INI file.
        """
        # Call the open_ini method to read the file and set the directory and server
        self.__directory, self.__server = self.open_ini(filename)
    
    def open_ini(self, filename: str):
        """
        Opens and reads the INI file to extract the directory and server details.

        Args:
            filename (str): The path to the INI file to be read.

        Returns:
            tuple: A tuple containing:
                - directory (str): The directory path found in the INI file.
                - server (str): The server connection string found in the INI file.
        """
        directory = None
        server = None
        # Open the file and read all lines
        with open(filename, "r") as file:
            content = file.readlines()
            
            # Process the first line for the directory
            trimmedcontent = content[0]
            if content[0].startswith("PATH"):
                directory = trimmedcontent.split("=")[1].strip()  # Extract directory path
                
            # Process the second line for the server
            trimmedcontent1 = content[1]
            if content[1].startswith("SERVER"):
                server = trimmedcontent1.split("=", 1)[1].strip()  # Extract server connection string
                
        return directory, server
    
    def get_directory(self):
        """
        Returns the directory path extracted from the INI file.

        Returns:
            str: The directory path.
        """
        return self.__directory
    
    def get_server(self):
        """
        Returns the server connection string extracted from the INI file.

        Returns:
            str: The server connection string.
        """
        return self.__server
