class IniManager:
    def __init__(self, filename):
        # Chiamata al metodo open_ini per leggere il file e settare la directory e il server
        self.__directory, self.__server = self.open_ini(filename)
    
    def open_ini(self, filename: str):
        directory = None
        server = None
        
        # Apri il file e leggi tutte le righe
        with open(filename, "r") as file:
            content=file.readlines()
            trimmedcontent= content[0]
            if content[0].startswith("PATH"):
                directory = trimmedcontent.split("=")[1].strip()
            trimmedcontent1 = content[1]
            if content [1].startswith("SERVER"):
                server = trimmedcontent1.split("=", 1)[1].strip() 
        return directory, server
    
    def get_directory(self):
        return self.__directory
    
    def get_server(self):
        return self.__server
