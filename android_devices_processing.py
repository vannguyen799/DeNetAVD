import logging
import os
import pathlib
import shutil
import subprocess
import time

HOME = str(pathlib.Path.home())
ANDROID_HOME = os.path.join(HOME, 'AppData/Local/Android/Sdk')
ADB = '"' + os.path.join(ANDROID_HOME, 'platform-tools/adb.exe') + '"'
EMULATOR = '"' + os.path.join(ANDROID_HOME, 'emulator/emulator.exe') + '"'
AVD_PATH = os.path.join(HOME, '.android/avd')

logging.debug(f'ADB: {ADB}')
logging.debug(f'EMULATOR: {EMULATOR}')
logging.debug(f'AVD_PATH: {AVD_PATH}')
logging.debug(f'ANDROID_HOME: {ANDROID_HOME}')


# ADB = 'adb'
# EMULATOR = 'emulator'


def clone_device(avd_name: str, src_avd_path='./resources/denet.avd', target='android-28'):
    clone_avd_path = f'./devices/{avd_name}'
    logging.info(f'Cloning device ---- {avd_name} --- ...')

    if not os.path.exists(clone_avd_path):
        os.makedirs(clone_avd_path)
    if not os.path.exists(clone_avd_path + '/userdata-qemu.img'):
        logging.info('Device not exist, cloning...')
        if not os.path.exists(src_avd_path):
            raise FileNotFoundError(f'AVD file not found at path: {src_avd_path}')
        shutil.rmtree(clone_avd_path)
        shutil.copytree(src_avd_path, clone_avd_path)
    else:
        logging.info(f'Device {avd_name} existed')
    logging.info(f'Register ini file for device {avd_name}...')
    avd_ini_path = f'{AVD_PATH}/{avd_name}.ini'
    new_init_content = f"""avd.ini.encoding=UTF-8
path={os.path.abspath(clone_avd_path)}
target={target}
"""

    if os.path.exists(avd_ini_path):
        with open(avd_ini_path, 'r') as f:
            existing_content = f.read()
    else:
        existing_content = ""

    if f'path={os.path.abspath(clone_avd_path)}' not in existing_content:
        with open(avd_ini_path, 'w') as f:
            f.write(new_init_content)

    logging.info(f'Cloning done --- {avd_name}')


def delete_device(device_name: str):
    try:
        logging.info(f'Deleting device {device_name}...')
        shutil.rmtree(f'./devices/{device_name}')
        os.remove(f'{HOME}/.android/avd/{device_name}')
    except Exception as e:
        logging.error(f'Error when deleting device {device_name}', e)
        pass


def get_connected_devices():
    """Returns a list of connected Android devices."""
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


def boot_device(avd_name, port=None, no_window=False, memory=4096, cores=2, snapshot_name=None, no_snapshot=False,
                no_snapshot_load=True,
                timeout=300):
    """
    Boot android device

    :return: emulator name
    """
    logging.info(f"Booting {avd_name}...")
    if port is None:
        port = select_available_port()
    cmd = f"{EMULATOR} -avd {avd_name} -memory {memory} -cores {cores} -port {port} -gpu host -no-boot-anim"  # -no-snapshot
    if no_window:
        cmd += " -no-window"
    if no_snapshot_load:
        cmd += " -no-snapshot-load"
    if no_snapshot:
        cmd += " -no-snapshot"
    if snapshot_name:
        cmd += f" -snapshot {snapshot_name}"
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

    # subprocess.run([ADB, "wait-for-device"])

    start_at = time.time()
    while time.time() - start_at < timeout:
        try:
            result = subprocess.run([ADB, "-s", emulator_name, "shell", "getprop", "sys.boot_completed"],
                                    capture_output=True, text=True, timeout=5)
        except subprocess.TimeoutExpired:
            continue

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
    for device in get_connected_devices():
        subprocess.run([ADB, '-s', device, 'emu', 'kill'])


def check_and_install_android_image(system_image="system-images;android-30;google_apis_playstore;x86"):
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


def list_snapshots(avd_name):
    """Returns a list of available snapshots for the given AVD."""
    try:
        # Run the adb command to list snapshots
        result = subprocess.run(
            ["adb", "-s", avd_name, "emu", "avd", "snapshot", "list"],
            capture_output=True,
            text=True,
            check=True
        )

        snapshots = result.stdout.strip().split("\n")
        snapshots = [snap.strip() for snap in snapshots if snap.strip()]

        return snapshots

    except subprocess.CalledProcessError as e:
        print(f"Error fetching snapshots: {e}")
        return []


def make_snapshot(device_name, snapshot_name):
    """Make snapshot of device
    Args:
        device_name:
        snapshot_name:
    Returns:
        snapshot name
    """
    os.system(f"{ADB} -s {device_name} emu avd snapshot save {snapshot_name}")
    return snapshot_name


def delete_snapshot(device_name, snapshot_name):
    os.system(f"{ADB} -s {device_name} emu avd snapshot delete {snapshot_name}")
