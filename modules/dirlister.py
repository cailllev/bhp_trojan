# python3 -c "import dirlister; print(dirlister.run())"
import os

def run(**args):
    print("[*] Running dirlister module")
    files = os.listdir(".")

    return str(files)
