import os
import logging
import pathlib
import shutil
import subprocess
import time

HOME = str(pathlib.Path.home())
ANDROID_HOME = os.path.join(HOME, 'AppData/Local/Android/Sdk')
ADB = '"' + os.path.join(ANDROID_HOME, 'platform-tools/adb.exe')+'"'
EMULATOR = '"' + os.path.join(ANDROID_HOME, 'emulator/emulator.exe') +'"'
AVD_PATH = os.path.join(HOME, '.android/avd')

# print(f'ANDROID_HOME: {ANDROID_HOME}')
# print(f'ADB: {ADB}')
# print(f'EMULATOR: {EMULATOR}')
# print(f'AVD_PATH: {AVD_PATH}')


def clone_device(avd_name, src_avd_path='./resources/denet.avd', target='android-28'):
    if not os.path.exists(src_avd_path):
        raise FileNotFoundError(f'AVD file not found at path: {src_avd_path}')
    clone_avd_path = f'./devices/{avd_name}'
    logging.info(f'Cloning device ---- {avd_name} --- ...')

    if not os.path.exists(clone_avd_path):
        os.makedirs(clone_avd_path)
    if not os.path.exists(clone_avd_path + '/userdata-qemu.img'):
        logging.info('Device not exist, cloning...')
        shutil.rmtree(clone_avd_path)
        shutil.copytree(src_avd_path, clone_avd_path)
    else:
        logging.info(f'Device {avd_name} existed')
    logging.info(f'Register ini file for device {avd_name}...')
    with open(f'{AVD_PATH}/{avd_name}.ini', 'w') as f:

        if f'path={os.path.abspath(clone_avd_path)}' not in f.read():
            f.write(f"""avd.ini.encoding=UTF-8
path={os.path.abspath(clone_avd_path)}
target={target}
""")



    # src = f"{HOME}/.android/adbkey.pub"
    # dst = f"{clone_avd_path}/data/misc/adb/adb_keys"
    # shutil.copyfile(src, dst)

    logging.info(f'Cloning done --- {avd_name}')


def delete_device(device_name):
    try:
        logging.info(f'Deleting device {device_name}...')
        shutil.rmtree(f'./devices/{device_name}')
        os.remove(f'{HOME}/.android/avd/{device_name}')
    except Exception as e:
        logging.error(f'Error when deleting device {device_name}', e)
        pass


def get_connected_devices():
    devices = os.popen(f'{ADB} devices').read().splitlines()[1:]  # Bỏ qua dòng đầu tiên
    return [device.split()[0] for device in devices if device.strip()]


# def clear_app_data(device_id, package_name):
#     try:
#         # Xóa dữ liệu ứng dụng
#         subprocess.run(['adb', '-s', device_id, 'shell', 'pm', 'clear', package_name], check=True)
#         print(f"Đã xóa dữ liệu của ứng dụng {package_name} trên thiết bị {device_id}")
#     except subprocess.CalledProcessError as e:
#         print(f"Lỗi khi xóa dữ liệu ứng dụng: {e}")
def clear_app_data(device_name, app_package):
    logging.info(f'Clearing {app_package} data for device {device_name}...')
    os.system(f'{ADB} -s {device_name} shell pm clear {app_package}')


def close_android(device_name):
    print(f'clossing android {device_name}')
    os.system(f"{ADB} -s {device_name} emu kill")
    time.sleep(1)


def boot_device(avd_name, port=None, no_window=False, memory=4096, cores=2, timeout=300):
    """
    Boot android device

    :return: emulator name
    """
    if port is None:
        port = select_available_port()
    cmd = f"{EMULATOR} -avd {avd_name} -memory {memory} -cores {cores} -port {port} -gpu host -no-boot-anim" #-no-snapshot
    if no_window:
        cmd += " -no-window"
    # os.system(cmd)
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    e_name = 'emulator-' + str(port)
    wait_for_emulator(e_name, timeout)

    try:
        subprocess.Popen([ADB, "-s", e_name, "shell", "settings", "put", "global", "window_animation_scale", "0"])
        subprocess.Popen([ADB, "-s", e_name, "shell", "settings", "put", "global", "transition_animation_scale", "0"])
        subprocess.Popen([ADB, "-s", e_name, "shell", "settings", "put", "global", "animator_duration_scale", "0"])
    except Exception:
        pass
    return e_name


def wait_for_emulator(emulator_name, timeout=300):
    logging.info(f"Waiting for {emulator_name} to be ready...")

    subprocess.run([ADB, "wait-for-device"])
    start_at = time.time()
    while time.time() - start_at < timeout:
        result = subprocess.run([ADB, "-s", emulator_name, "shell", "getprop", "sys.boot_completed"],
                                capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == "1":
            logging.info(f"{emulator_name} is ready!")
            return
        logging.debug(f"Waiting for {emulator_name} to boot...")
        time.sleep(2)

    raise TimeoutError(f"Timed out waiting for {emulator_name} to boot.")


def select_available_port():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def close_all_android_emulators():
    output = subprocess.check_output([ADB, 'devices']).decode('utf-8')
    emulator_devices = [line.split('\t')[0] for line in output.split('\n') if 'emulator' in line]
    for device in emulator_devices:
        subprocess.run([ADB, '-s', device, 'emu', 'kill'])


def check_and_install_android_image(system_image = "system-images;android-30;google_apis_playstore;x86"):
    if not shutil.which("sdkmanager"):
        print("Error: sdkmanager not found. Ensure Android SDK is installed and added to PATH.")
        return

    result = subprocess.run(
        ["sdkmanager", "--list"], capture_output=True, text=True, shell=True
    )

    if system_image in result.stdout:
        return

    subprocess.run(["sdkmanager", system_image], shell=True, check=True)

    subprocess.run('yes | sdkmanager --licenses', shell=True, check=True)

