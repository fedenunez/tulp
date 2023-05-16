import os
from . import tulplogger
log = tulplogger.Logger()

class TulpOutputFileWriter:
    def __init__(self):
        pass

    def write_to_file(self, file_name, content):
        """
        Writes the given content to the given file name. If the file already exists, it will rename it to a new file on the same folder, appending to the file name a counter (like -1) and keeping the same extension. It will continually increase the counter until it finds a free object.

        :param file_name: The name of the file to write to.
        :param content: The content to write to the file.
        :return: True and the filename on success, False otherwise.
        """
        if os.path.exists(file_name):
            file_name_parts = os.path.splitext(file_name)
            counter = 0
            new_file_name = file_name
            while os.path.exists(new_file_name):
                counter += 1
                new_file_name = f"{file_name_parts[0]}.backup-{counter}{file_name_parts[1]}"
            if counter > 0 :
                os.rename(file_name, new_file_name)
                log.warning(f"Output file already exists, moving the existing file to {new_file_name}")
        try:
            with open(file_name, "w") as f:
                f.write(content)
            return True, file_name
        except Exception as e:
            return False, str(e)
