import threading


class HandleExcelUpload(threading.Thread):
    def __init__(self, reader, depot):
        self.reader = reader
        self.depot = depot

        threading.Thread.__init__(self)

    def run(self):
        pass
