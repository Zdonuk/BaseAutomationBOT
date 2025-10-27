from datetime import datetime
from colorama import Fore
import os

class Logger():

    def __init__(self):
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
        if not os.path.exists(logs_dir):
            os.mkdir(logs_dir)

        self.filename = os.path.join(logs_dir, f"{current_time}.txt")

        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='UTF-8') as file:
                file.write(f'Запуск в {current_time}\n')

    def get_current_time(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        return f'[{current_time}] '

    def add_log(self, message):
        with open(self.filename, 'a', encoding='UTF-8') as file:
            file.write('\n' + message)

    def _log(self, message, level, wallet, print_out=True):
        wallet = f"[{wallet[:5]}...{wallet[-5:]}] " if wallet else ''
        current_time = self.get_current_time()

        log_message = f"{current_time}"
        colored_message = f"{Fore.WHITE}{current_time}"

        if level == 0:
            log_message += f"[INFO] {wallet}{message}"
            colored_message += f"{Fore.WHITE}[INFO] {wallet}{message}{Fore.WHITE}"
        elif level == 1:
            log_message += f"[WARNING] {wallet}{message}"
            colored_message += f"{Fore.YELLOW}[WARNING] {wallet}{message}{Fore.WHITE}"
        elif level == 2:
            log_message += f"[ERROR] {wallet}{message}"
            colored_message += f"{Fore.RED}[ERROR] {wallet}{message}{Fore.WHITE}"
        elif level == 3:
            log_message += f"[SUCCESS] {wallet}{message}"
            colored_message += f"{Fore.GREEN}[SUCCESS] {wallet}{message}{Fore.WHITE}"

        if print_out:
            print(colored_message)
        self.add_log(log_message)

    def log(self, message, wallet = None, print_out = True):
        self._log(message, 0, wallet, print_out=print_out)

    def log_warning(self, message, wallet = None, print_out = True):
        self._log(message, 1, wallet, print_out=print_out)

    def log_error(self, message, wallet = None, print_out = True):
        self._log(message, 2, wallet, print_out=print_out)

    def log_success(self, message, wallet = None, print_out = True):
        self._log(message, 3, wallet, print_out=print_out)

