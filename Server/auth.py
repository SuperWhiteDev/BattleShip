
from hashlib import sha256
from colorama import Fore, Style, init as init_colorama
from os import path

init_colorama()

class Authentication:
    class TestError(Exception):
        """Exception for password testing errors"""
        pass

    AUTH_FILE = "auth.enc"
    FIRST_AUTH = True

    @staticmethod
    def _set(password : str) -> None:
        """
        Saves the SHA-256 hashed password to a file.
        """
        hashed_password = sha256(password.encode()).hexdigest()
        with open(Authentication.AUTH_FILE, "w") as f:
            f.write(hashed_password)

    @staticmethod
    def is_available() -> bool:
        """
        Return if the file with the password exists.
        """
        return path.exists(Authentication.AUTH_FILE)

    @staticmethod
    def _match(password : str) -> bool:
        """
        Checks if the entered password matches the saved password hash.
        """
        if not Authentication.is_available():
            raise FileNotFoundError(f"Password file {Authentication.AUTH_FILE} not found!")

        password = sha256(password.encode()).hexdigest()

        with open(Authentication.AUTH_FILE, "r") as f:
            saved_password = f.read()
        
        return password == saved_password
    
    def is_first_auth() -> bool:
        return Authentication.is_first_auth

    def login(out_function, in_function) -> bool:
        password = in_function("Enter your password: ")
        
        if password and Authentication._match(password):
            if Authentication.FIRST_AUTH:
                out_function(Fore.GREEN + "You have successfully logged in as admin." + Style.RESET_ALL)
                Authentication.FIRST_AUTH = False

            return True
        else:
            return False
        
    def _validate_password(password : str, out_function, in_function) -> bool:
        if type(password) != str:
            raise Authentication.TestError("Test #0. The password must be a string!")
        
        if len(password) >= 8:
            out_function(Fore.GREEN + "Test #1. Password length is greater than or equal to eight" + Style.RESET_ALL)
        else:
            raise Authentication.TestError(Fore.RED + "The password length is less than eight characters!" + Style.RESET_ALL)
    
        if any(char.isupper() for char in password):
            out_function(Fore.GREEN + "Test #2. The password contains at least one uppercase character" + Style.RESET_ALL)
        else:
            raise Authentication.TestError(Fore.RED + "The password does not contain at least one uppercase character!" + Style.RESET_ALL)

        if any(char.isdigit() for char in password):
            out_function(Fore.GREEN + "Test #3. The password contains at least one digit." + Style.RESET_ALL)
        else:
            raise Authentication.TestError(Fore.RED + "The password does not contain at least one number!" + Style.RESET_ALL)

        return True

    def register(out_function, in_function) -> None:
        while True:
            password = in_function("Enter your password to log in to the admin panel later: ")
            if not Authentication.is_first_auth():
                return
        
            try:
                Authentication._validate_password(password, out_function, in_function)
            except Authentication.TestError as e:
                out_function(Fore.RED + f"Test failed: {e}" + Style.RESET_ALL + "\n")
            else:
                confirm_password = in_function("Enter your password again to confirm it: ")
                if not Authentication.is_first_auth():
                    return
        
                if confirm_password == password:
                    Authentication._set(password)
                    Authentication.FIRST_AUTH = False
                    out_function(Fore.GREEN + "The password has been successfully confirmed and set" + Style.RESET_ALL)
                    return
                else:
                    out_function(Fore.RED + "Your entered passwords do not match!" + Style.RESET_ALL)
                    continue