from sys import exit
from configparser import ConfigParser

superuser = ConfigParser()
superuser.read("superuser.ini")


if __name__ == "__main__":
    del superuser
    from secrets import token_bytes

    superuser = ConfigParser()
    superuser.add_section("superuser")
    superuser.set("superuser", "username", "admin")
    superuser.set("superuser", "password", token_bytes(32).hex())
    superuser.write(open("superuser.ini", mode="w", encoding="utf-8"))
    print("Edit the user name and password in superuser.ini!"), exit(0)
