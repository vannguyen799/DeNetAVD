import logging
import os

from DeNet import get_accounts_from_txt, avd_name_from_acc, DEVICE_PATH
from android_devices_processing import clone_device

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
acc_s = get_accounts_from_txt()

CLEAR_OLD = input('Clear old device unused (enter 1):') == 1

if CLEAR_OLD:
    for subdir in [name for name in os.listdir(DEVICE_PATH) if os.path.isdir(os.path.join(DEVICE_PATH, name))]:
        if subdir not in [avd_name_from_acc(acc) for acc in acc_s]:
            os.remove(os.path.join(DEVICE_PATH, subdir))
            
for acc in acc_s:
    clone_device(avd_name_from_acc(acc))
