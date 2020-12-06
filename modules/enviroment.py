# python3 -c "import enviroment; print(enviroment.run())"
import os

def run(**args):
    print("[*] Running enviroment module")
    return str(os.environ)
