# -*- coding: utf-8 -*-
from dataclasses import dataclass
from frameworks.browser_control import Chrome
from frameworks.decorators.decorators import retry
from frameworks.desktop import Package, DesktopEditor, DesktopData

import time
from frameworks.StaticData import StaticData

from os.path import join, dirname, realpath
from frameworks.host_control import FileUtils, HostInfo
from frameworks.image_handler import Image
from rich import print

from selenium.webdriver.chrome.options import Options
from pyvirtualdisplay import Display

from frameworks.telegram import Telegram
from tests.tools.desktop_report import DesktopReport


@dataclass(frozen=True)
class XPath:
    hello_document: str = '//*[@id="items"]/p/a/div'

class DesktopTest:
    def __init__(self, version: str, sudo_password: str = None):
        self.version = version
        self.report = DesktopReport(StaticData.reports_dir, self.version)
        self.package = Package(DesktopData(tmp_dir=StaticData.tmp_dir, version=self.version, cache_dir=StaticData.cache_dir), sudo_password=sudo_password)
        self.desktop = DesktopEditor(debug_mode=True)
        self.display = Display(visible=0, size=(1920, 1080))
        self.display.start()
        self.chrome = Chrome(chrome_options=self._chrome_options())
        self.exceptions: list = FileUtils.read_json(join(dirname(realpath(__file__)), 'assets', 'console_exceptions.json'))['console_exceptions']

    @staticmethod
    def _chrome_options():
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        return chrome_options


    def run(self):
        self.package.get()
        self.check_installed()
        self.desktop.open()
        self.check_errors()
        self._write_results(f'Passed')
        self.desktop.close()
        self.chrome.close()
        self.display.stop()

    def check_errors(self):
        self.connection_debug_mode()
        time.sleep(5)
        errors = self.check_console_log()
        if errors:
            self._write_results(f'console_errors: {errors}')
            raise print(f"[bold red]|ERROR| OnOnlyOffice Desktop opens with errors in the js console")

    @retry(max_attempts=50, interval=2, stdout=False)
    def connection_debug_mode(self):
        self.chrome.open('http://127.0.0.1:8080')
        self.chrome.click_by_xpath(XPath.hello_document)


    def check_console_log(self) -> list:
        js_logs = self.chrome.get_js_log()
        self.chrome.driver.execute_script("console.clear();")
        errors = []
        for log in js_logs:
            if log['message'] in self.exceptions:
                print(f"[green]|CONSOLE LOG| {log['message']}")
            else:
                errors.append(log['message'])
                print(f"[bold red]{'-'*90}\n|CONSOLE LOG||ERROR| {log['message']}\n{'-'*90}")
        return errors


    def check_installed(self):
        installed_version = self.package.get_version()
        if self.version != installed_version:
            self._write_results('NOT_INSTALLED')
            raise print(
                f"[bold red]|ERROR| OnlyOffice Desktop not installed. "
                f"Current version: {installed_version}"
            )

    def _write_results(self, results):
        desktop_screen = join(StaticData.reports_dir, f'{self.version}_{HostInfo().name(pretty=True)}_desktop_screen.png')
        Image.make_screenshot(f"{desktop_screen}")
        browser_screen = join(StaticData.reports_dir, f'{self.version}_{HostInfo().name(pretty=True)}_browser_screen.png')
        self.chrome.make_screenshot(browser_screen)
        Telegram().send_media_group(
            document_paths=[desktop_screen, browser_screen],
            caption=f'Package: `{self.package.name.replace("_", "-")}`\n'
            f'Version: `{self.version}`\n'
            f'Os: `{HostInfo().name(pretty=True)}`\n'
            f'Result: `{results}`',
            media_type='photo'
        )
        self.report.write(self.package.name, self.version, HostInfo().name(pretty=True), results)
