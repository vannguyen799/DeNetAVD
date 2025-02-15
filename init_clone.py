import os
import shutil

from android_devices_processing import AVD_PATH,HOME
with open(f'{AVD_PATH}/denet.ini', 'w') as f:
    f.write(f"""avd.ini.encoding=UTF-8
path={os.path.abspath('./resources/denet.avd')}
target=android-30""")


