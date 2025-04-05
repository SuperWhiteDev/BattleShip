import subprocess
import platform
from random import random

def get_uuid() -> str:
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output(["wmic", "csproduct", "get", "uuid"], encoding='utf-8')
            return output.split("\n")[2].strip()
        except Exception:
            pass
    elif platform.system() == "Linux":
        return subprocess.check_output(["cat", "/etc/machine-id"]).strip().decode('utf-8')
    elif platform.system() == "Darwin":
        return subprocess.check_output(["system_profiler", "SPHardwareDataType"]).decode('utf-8').split("UUID:")[1].strip().split("\n")[0]
    
    return str(random())