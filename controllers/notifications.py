from notifypy import Notify


class Notifier:
    def __init__(self):
        pass

    def send(self, title , text):
        notif = Notify()
        notif.message = text
        notif.title = title
        notif.send()