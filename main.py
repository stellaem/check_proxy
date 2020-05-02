import sys
import threading
from fake_useragent import UserAgent
import requests
from bs4 import BeautifulSoup
from PySide2.QtCore import QObject, QResource, QFile, QThread
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication


white_list = []
URL = 'https://psyrazvitie.ru'


class MainObject(QObject):
    def __init__(self):
        super().__init__()
        QResource.registerResource('resources.rcc')
        ui_file = QFile('ui_files/ui_MainWindow.ui')
        ui_file.open(QFile.ReadOnly)
        self.window = QUiLoader().load(ui_file)
        ui_file.close()


class MainWindow(MainObject):
    def __init__(self):
        super().__init__()
        self.proxy_list = []
        self.window.button_start.clicked.connect(self.start_find_proxy)
        self.window.button_stop.clicked.connect(self.stop_find_proxy)
        self.window.button_save.clicked.connect(self.save_proxy_list)
        self.window.show()

    def start_find_proxy(self):
        white_list.clear()
        self.window.list_proxy.clear()
        self.thread = ThreadFromApp(parent=self)
        self.thread.terminate()
        self.thread.start()

    def stop_find_proxy(self):
        self.thread.terminate()
        self.thread.stop()

    def save_proxy_list(self):
        with open('proxy.txt', 'tw', encoding='utf-8') as f:
            for item in white_list:
                f.write("%s\n" % item)


class ThreadFromApp(QThread):
    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent
        self.proxy_list = []

    def __del__(self):
        self.wait()

    def run(self):
        self.list_thread = []
        for i in range(10):
            self.list_thread.append(ThreadBruteForce(parent=self, i=i + 1))
        for thread in self.list_thread:
            thread.start()
        for thread in self.list_thread:
            thread.join()

    def stop(self):
        for thread in self.list_thread:
            thread.killed = True

    def show_check_proxy(self, message):
        self.parent.window.statusbar.clearMessage()
        self.parent.window.statusbar.showMessage(message)

    def add_proxy_to_list(self, proxy):
        self.parent.window.list_proxy.insertItem(-1, proxy)


class ThreadBruteForce(threading.Thread):
    def __init__(self, parent, i):
        super().__init__()
        self.killed = False
        self.parent = parent
        self.num_list = i
        self.url = self.get_url()

    def get_url(self):
        if self.num_list == 1:
            return 'https://www.my-proxy.com/free-proxy-list.html'
        else:
            return f'https://www.my-proxy.com/free-proxy-list-{self.num_list}.html'

    def run(self):
        r = requests.get(self.url, timeout=5, headers={'User-Agent': UserAgent().chrome})
        if r.ok:
            self.get_data(r.text)
        else:
            print(r.ok)

    def get_data(self, html):
        soup = BeautifulSoup(html, 'lxml')
        proxy = soup.find('div', class_="list")
        for el in proxy:
            if el == soup.br:
                el.replace_with('\n')
            if el == soup.find('div', class_='to-lock'):
                for el2 in el:
                    if el2 == soup.br:
                        el2.replace_with('\n')
        proxy.text.split('\n')
        self.proxy_list = [line.split("#")[0] for line in proxy.text.split('\n')]
        self.valid_proxy()

    def valid_proxy(self):
        for proxy in self.proxy_list:
            if self.killed is False:
                try:
                    self.parent.show_check_proxy(f'проверяю {proxy}')
                    r = requests.get(URL, proxies={'http': proxy, 'https': proxy}, timeout=5)
                    if r.ok:
                        if proxy != str(''):
                            self.parent.add_proxy_to_list(proxy)
                            white_list.append(proxy)
                except:
                    pass
            else:
                self.parent.show_check_proxy('остановленно')
        self.parent.show_check_proxy('проверка выполнена')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
