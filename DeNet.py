import logging
import os
import random
import string
import time

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from android_devices_processing import clear_app_data, clone_device, boot_device, close_android, \
    get_connected_devices

##########################################################
DEFAULT_ANDROID_AVD = r'C:\Users\Veer 2\.android\avd\Medium_Phone_API_28.avd'
ANDROID_TARGET = 'android-28'

DEVICE_PATH = './devices'
LOG_PATH = './logs'

APPIUM_SERVER_URL = 'http://127.0.0.1:4723'
DEFAULT_ELEMENT_TIMEOUT = 200
ACCOUNT_CLAIM_SLEEP = 60 * 60 * 6  # 6 HOUR
SLEEP_CHECK = 30 * 60  # 30 MIN
ANDROID_RAM = 8  # GB
ANDROID_CORES = 4
ONE_DEVICE_MODE = False
ANDROID_BOOT_TIMEOUT = 3 * 60  # 3 MIN
##########################################################

account_processing_in4: dict[str, int] = {}  # list(account, last_process_time) )

CLEAR_OLD = False
HEADLESS = False

os.makedirs(LOG_PATH, exist_ok=True)
os.makedirs(DEVICE_PATH, exist_ok=True)


def check_appium_server():
    import requests
    try:
        requests.get(APPIUM_SERVER_URL)
        return True
    except requests.exceptions.ConnectionError:
        pass


def generate_password(length=9):
    if length < 3:
        raise ValueError("Password length must be at least 3 to include all required character types.")

    uppercase = random.choice(string.ascii_uppercase)
    lowercase = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)

    other_chars = random.choices(string.ascii_letters + string.digits, k=length - 3)

    password = list(uppercase + lowercase + digit + ''.join(other_chars))
    random.shuffle(password)

    return ''.join(password)


def initialize_driver(device_name):
    capabilities = dict(
        platformName='Android',
        automationName='UiAutomator2',
        deviceName=device_name,
        enforceXPath1=True,  # Fixes accessibility issues
        newCommandTimeout=300,  # Prevents session timeout
        uiautomator2ServerLaunchTimeout=90 * 1000,  # Increases UIAutomator2 startup time
        uiautomator2ServerInstallTimeout=120 * 1000,  # Increases UIAutomator2 installation time
        disableWindowAnimation=True,  # Reduces lag
    )
    # appium_server_url = 'http://localhost:4723/wd/hub'
    capabilities_options = UiAutomator2Options().load_capabilities(capabilities)

    driver = webdriver.Remote(command_executor=APPIUM_SERVER_URL, options=capabilities_options)
    return driver


def load_device_by_account(account: str):
    """

    :param account:
    :return: device name
    """
    if ONE_DEVICE_MODE:
        return get_connected_devices()[0]

    avd_name = avd_name_from_acc(account)
    clone_device(avd_name, src_avd_path=DEFAULT_ANDROID_AVD, target=ANDROID_TARGET)
    return boot_device(avd_name, memory=int(ANDROID_RAM * 1024), cores=ANDROID_CORES, timeout=ANDROID_BOOT_TIMEOUT)


class DeNetTool:
    device_name: str
    driver: WebDriver
    account: str

    def setUp(self) -> None:
        self.device_name = avd_name_from_acc(self.account)
        self.device_name = load_device_by_account(self.account)
        time.sleep(5)

        self.driver = initialize_driver(self.device_name)

    def tearDown(self) -> None:
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            pass
        if not ONE_DEVICE_MODE:
            close_android(self.device_name)

    def test_open_tiktok(self, force=False):

        package_name = "pro.denet.storage"
        if force or ONE_DEVICE_MODE:
            clear_app_data(self.device_name, package_name)
        account = self.account
        try:
            logging.info(f"Running Account: {account}")
            email, password, code = account.split(":", 2)  # Tách email, password và code
            password = password or generate_password(length=9)

            time.sleep(5)
            self.driver.press_keycode(3)  # Keycode 3 là Home button
            time.sleep(2)
            app_value = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, '//android.widget.TextView[@content-desc="DeNet Storage"]'))
            )
            app_value.click()

            # fix notification # android 15
            # popup = WebDriverWait(self.driver, 5).until(
            #     EC.presence_of_element_located((AppiumBy.XPATH, "//android.widget.TextView[contains(@text, 'otification')]"))
            # )
            # if popup:
            #     allow = WebDriverWait(self.driver, 3).until(
            #         EC.presence_of_element_located(
            #             (AppiumBy.XPATH, "//android.widget.Button[@text='Allow']"))
            #     )
            #     allow.click()
            time.sleep(5)

            passcode_btn = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, f'//android.widget.TextView[@text="1" or @text="Continue"]'))
            )
            logging.info('Open App Success: {}'.format(passcode_btn.text))
            if passcode_btn.text == 'Continue':
                logging.info('Importing accounts...')

                # clear_app_data(self.device_name, package_name)
                # self.driver.press_keycode(3)  # Keycode 3 là Home button
                time.sleep(2)
                # app_value = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                #     EC.presence_of_element_located(
                #         (AppiumBy.XPATH, '//android.widget.TextView[@content-desc="DeNet Storage"]'))
                # )
                # app_value.click()

                Continue_Click = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, '//android.widget.TextView[@text="Continue"]'))
                )

                Continue_Click.click()

                time.sleep(1)
                Continue_Click1 = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, '//android.widget.TextView[@text="Continue"]'))
                )
                Continue_Click1.click()
                time.sleep(1)
                Continue_Click1 = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                    EC.presence_of_element_located(
                        (AppiumBy.XPATH, '//android.widget.TextView[@text="Import account"]'))
                )
                Continue_Click1.click()
                time.sleep(1)
                email_field = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                    EC.presence_of_element_located(
                        (AppiumBy.XPATH, '//android.widget.EditText[@text="Enter private key"]'))
                )
                email_field.click()
                time.sleep(1)
                email_field.send_keys(email)

                time.sleep(1)
                password_field1 = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                    EC.presence_of_element_located(
                        (AppiumBy.XPATH, '(//android.widget.EditText[@text="Enter password"])[1]'))
                )
                password_field1.click()
                time.sleep(1)
                password_field1.send_keys(password)
                time.sleep(1)
                password_field2 = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                    EC.presence_of_element_located(
                        (AppiumBy.XPATH, '//android.widget.EditText[@text="Enter password"]'))
                )
                password_field2.click()
                time.sleep(1)
                password_field2.send_keys(password)
                time.sleep(1)
                self.driver.hide_keyboard()  # fix keyboard over Next btn

                Click_field2 = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                    EC.presence_of_element_located((AppiumBy.XPATH,
                                                    '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.widget.Button'))
                )
                Click_field2.click()
                time.sleep(5)
                for char in code:
                    Click_fieldz = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((AppiumBy.XPATH, f'//android.widget.TextView[@text="{char}"]'))
                    )
                    Click_fieldz.click()
                    time.sleep(1)
                time.sleep(2)
                for char in code:
                    Click_fieldz = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((AppiumBy.XPATH, f'//android.widget.TextView[@text="{char}"]'))
                    )
                    # Thực hiện click
                    Click_fieldz.click()
                    time.sleep(1)  # Thêm thời gian chờ giữa các lần click nếu cần
            else:
                logging.info(f'Enter passcode: {code}')
                for char in code:
                    Click_fieldz = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((AppiumBy.XPATH, f'//android.widget.TextView[@text="{char}"]'))
                    )
                    Click_fieldz.click()
                    time.sleep(1)

                # FIX WRONG PASSCODE
                # try:
                #     Click_fieldz = WebDriverWait(self.driver, DEFAULT_ELEMENT_TIMEOUT).until(
                #         EC.presence_of_element_located((AppiumBy.XPATH,'//android.widget.TextView[@text="Watcher")]'))
                #     )
                # except Exception as e:
                #     Click_fieldz = None
                # if not Click_fieldz:
                #     logging.info(f'Wrong passcode: RELOGIN')
                #     # return
                #     return self.test_open_tiktok(True)

            time.sleep(5)

            try_claim(driver=self.driver)

            print(f"Tài Khoản Đã Turn On {account} ")
            with open(os.path.join(LOG_PATH, f'{avd_name_from_acc(account)}_last_log.txt'), 'a') as file:
                file.write(f"OK")
            save_last_timestamp(account, time.time())

        except Exception as e:
            print(f"Lỗi với tài khoản {account}: {e}")

            with open(os.path.join(LOG_PATH, f'{avd_name_from_acc(account)}_last_log.txt'), 'a') as file:
                file.write(f"Error: {e}")
            # delete_device(account)
            self.tearDown()
            # close_android(self.device_name)
            return

    def scroll_up(self):
        screen_size = self.driver.get_window_size()
        start_x = screen_size['width'] / 2
        start_y = screen_size['height'] * 0.8
        end_y = screen_size['height'] * 0.2
        self.driver.swipe(start_x, start_y, start_x, end_y, 800)
        print("Cuộn lên thành công.")


# Hàm để lấy tài khoản từ Google Sheets
def get_accounts_from_txt():
    accounts = []
    try:
        with open('accounts.txt', 'r') as file:
            # Đọc từng dòng và thêm tài khoản vào danh sách
            for line in file:
                line = line.strip()  # Loại bỏ khoảng trắng thừa
                if line:
                    accounts.append(line)
    except FileNotFoundError:
        print("File accounts.txt không tồn tại.")
        exit(1)
    return accounts


def avd_name_from_acc(account):
    return account.split(":")[0] + '.avd'


def try_claim(driver: WebDriver):
    try:
        Click_fieldx = WebDriverWait(driver, DEFAULT_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located((AppiumBy.XPATH,
                                            '//android.widget.TextView[@text="Turn on" or contains(@text,"LAUNCH TO EARN") or contains(@text,"CHARGE REQUIRED")]'))
        )
        if Click_fieldx.text == 'Turn on':
            Click_fieldx.click()
            time.sleep(5)
            Click_fieldx = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((AppiumBy.XPATH,
                                                '//android.widget.TextView[contains(@text,"LAUNCH TO EARN")]'))
            )

        if 'CHARGE REQUIRED' not in Click_fieldx.text:
            Click_fieldx.click()
            time.sleep(10)

    except Exception as e:
        pass


def save_last_timestamp(acc, last_timestamp):
    account_processing_in4[acc] = last_timestamp

    with open(os.path.join(LOG_PATH, f'{avd_name_from_acc(acc)}_last_timestamp.txt'), 'w') as file:
        file.write(str(last_timestamp))


def last_timestamp_of(acc):
    timestamp_file = os.path.join(LOG_PATH, f'{avd_name_from_acc(acc)}_last_timestamp.txt')
    last_timestamp = 0
    if os.path.exists(timestamp_file) and os.path.getsize(timestamp_file) > 0:
        with open(timestamp_file, 'r') as file:
            last_timestamp = float(file.read().strip())
    else:
        with open(timestamp_file, 'w') as file:
            file.write(str(last_timestamp))

    account_processing_in4[acc] = last_timestamp
    return last_timestamp


# Hàm chạy công cụ với danh sách tài khoản
def run_tool(accounts):
    global account_processing_in4
    for acc in accounts:
        account_processing_in4[acc] = last_timestamp_of(acc)

    while True:
        for account, last_timestamp in account_processing_in4.items():
            now = time.time()
            if now - last_timestamp > ACCOUNT_CLAIM_SLEEP:
                logging.info('Account Index: ', accounts.index(account))

                try:
                    denet = DeNetTool()
                    denet.account = account
                    try:
                        denet.setUp()
                        denet.test_open_tiktok()
                    except Exception as e:
                        logging.error(f'DeNetTool err: {account} {e}')
                    finally:
                        denet.tearDown()
                except Exception as e:
                    logging.error(f'Account err: {account} {e}')
                logging.info(f"Done in {int((time.time() - now) / 60)} minutes.")
                time.sleep(5)  # small sleep for prev close android timeout

        logging.info(f"Waiting for {SLEEP_CHECK} seconds...")
        time.sleep(SLEEP_CHECK)


def main():
    global CLEAR_OLD, HEADLESS
    accounts = get_accounts_from_txt()

    if not accounts:
        print("Không có tài khoản trong Google Sheets.")
        exit(1)

    CLEAR_OLD = input('Clear old device unused (enter 1):') == '1'
    HEADLESS = input('Run headless (enter 1):') == '1'
    if CLEAR_OLD:
        accounts_name = [avd_name_from_acc(account) for account in accounts]
        for subdir in [name for name in os.listdir(DEVICE_PATH) if os.path.isdir(os.path.join(DEVICE_PATH, name))]:
            if subdir not in accounts_name:
                os.remove(os.path.join(DEVICE_PATH, subdir))

    try:
        if not check_appium_server():
            raise Exception("Appium server not running...")
        # check_and_install_android_image()

        run_tool(accounts)
    except Exception as e:
        logging.error(f"Error all: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s\t%(message)s')
    main()
