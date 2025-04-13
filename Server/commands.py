from time import sleep
from user import User
from game_session import Session
from data import Data

class Commands:
    def _command(command_function):
        def wrapper(server, command):
            try:
                return command_function(server, *Commands._parse_command(command))
            except Exception as e:
                return None
        return wrapper
    
    def _parse_command(command : str) -> tuple[list[str], dict]:
        args = []
        kwargs = {}

        command = command.split(maxsplit=1)
        if len(command) == 2:
            command = command[1]
            arguments = command.replace("<", " ").replace(">", " ").split()
            for arg in arguments:
                arg = arg.split("=")
                if len(arg) == 2:
                    kwargs[arg[0]] = arg[1]
                else:
                    args.append(arg[0])
        
        return args, kwargs
    
    @staticmethod
    @_command
    def help(server, args, kwargs) -> str:
        return """
Available commands: 
    1. users,
    2. ban-list,
    3. white-list,
    4. sessions,
    5. ban <user_name>,
    6. unban <user_name>,
    7. disconnect <user_name>,
    8. stop-session <id>,
    9. delete-data,
    10. all-users,
    11. delete-user <user_name>,
    12. add-admin-user <user_name>
    13. stop,
    14. restart
Example:
    ban SomeUserName
    
    stop-session 0
    
    restart
"""

    @staticmethod
    @_command
    def users_list(server, args, kwargs) -> str:
        # Вывод списка активных пользователей

        output = ""
        
        users : set = User.get_users(server)
        if len(users) > 0:
            output += "Connected users:\n"
            for i, user in enumerate(users):
                output += f"{i + 1}. {user.name.capitalize()} (ID: {user.id}, IP: {user.get_ip_address()}) Logged in: {user.is_logged()}\n"
            output += "\n"
        else:
            output += "No connected clients"

        return output
    
    @staticmethod
    @_command
    def ban_list(server, args, kwargs) -> str:
        output = ""

        black_list = server.server_data.black_list.get()
        if len(black_list) > 0:
            output += "Blocked users:\n"
            for i, user in enumerate(black_list):
                output += f"{i + 1}. {user["user_name"].capitalize()} (HID: {user["user_id"]})"
            output += "\n"
        else:
            output += "No blocked users yet."

        return output
    
    @staticmethod
    @_command
    def white_list(server, args, kwargs) -> str:
        output = ""

        white_list = server.server_data.white_list.get()
        if len(white_list) > 0:
            output += "Privileged users:\n"
            for i, user in enumerate(white_list):
                permission = user["permission"]
                if permission == 0:
                    permission = "Admin"

                output += f"{i + 1}. {user["user_name"].capitalize()} (Privilege level: {permission})"
            output += "\n"
        else:
            output += "No privileged users yet."

        return output
    
    @staticmethod
    @_command
    def sessions_list(server, args, kwargs) -> str:
        output = ""

        if len(Session.sessions):
            output += "Active Game Sessions:"

            for i, session in enumerate(Session.sessions):
                players = "\n"
                for i, player in enumerate(session.players):
                    players += f"{i+1}. '{player.name}'\n"
                output += f"{i+1}. Session #{session.id}. Players: {players}"
        else:
            output += "No active sessions"

        return output
    
    @staticmethod
    @_command
    def ban_user(server, args, kwargs) -> str:
        output = ""

        user_name = kwargs.get("user_name") or (args[0] if args else None)
        if user_name:
            user = User.get_user_by_name(server, user_name)
            if user:
                user.ban()
                output += f"The User with name {user_name} has been banned."
            else:
                output += f"Failed to ban user with name {user_name}."
        else:
            output += "Error: Specify a valid user name to ban (e.g., 'ban <user_name>')."

        return output
    
    @staticmethod
    @_command
    def unban_user(server, args, kwargs) -> str:
        output = ""

        user_name = kwargs.get("user_name") or (args[0] if args else None)
        if user_name:
            if server.server_data.black_list.remove(user_name):
                output += f"The User with name {user_name} has been unbanned."
            else:
                output += f"Failed to unban user with name {user_name}."
        else:
            output += "Error: Specify a valid user name to unban (e.g., 'unban <user_name>')."

        return output
    
    @staticmethod
    @_command
    def disconnect_user(server, args, kwargs) -> str:
        output = ""

        user_name = kwargs.get("user_name") or (args[0] if args else None)
        if user_name:
            user = User.get_user_by_name(server, user_name)
            if user:
                user.disconnect_user()
        else:
            output += "Error: Specify a valid user name to disconnect (e.g., 'disconnect <user_name>')."

        return output

    @staticmethod
    @_command
    def stop_session(server, args, kwargs) -> str:
        output = ""

        id = kwargs.get("id") or (args[0] if args else None)
        if id:
            if id >= 0 and id < len(Session.sessions):
                Session.sessions[id].Stop()
                output += "Succesfully complete."
            else:
                output += "Error: Specify a valid session id to close it."
        else:        
            output += "Error: Specify the session id to close (e.g., 'stop-session <id>')."

        return output
    
    @staticmethod
    @_command
    def delete_data(server, args, kwargs) -> str:
        output = ""
        
        if server.server_data.delete_data():
            output += "The data in the database has been successfully deleted."
        else:
            output += "Failed to delete data in the database."

        return output
    
    @staticmethod
    @_command
    def all_users(server, args, kwargs) -> str:
        output = ""

        users = server.server_data.users.get()
        if len(users) > 0:
            output += "Registred users:\n"
            for i, user in enumerate(users):
                output += f"{i + 1}. {user["user_name"].capitalize()}. Since: {user["register_date"]}\n"
            output += "\n"
        else:
            output += "No registred users yet."

        return output
    
    @staticmethod
    @_command
    def delete_user(server, args, kwargs) -> str:
        output = ""

        user_name = kwargs.get("user_name") or (args[0] if args else None)
        if user_name:
            if server.server_data.users.remove(user_name):
                output += f"The User with name {user_name} has been deleted from database."
            else:
                output += f"Failed to delete user with name {user_name}."
        else:
            output += "Error: Specify a valid user name to delete (e.g., 'delete-user <user_name>')."

        return output

    @staticmethod
    @_command
    def add_admin_user(server, args, kwargs) -> str:
        output = ""

        user_name = kwargs.get("user_name") or (args[0] if args else None)
        if user_name:
            server.server_data.white_list.add(user_name, 0)
            output += f"The user with name {user_name} has been added as an admin."
        else:
            output += "Error: Specify a valid user name to add-admin-user (e.g., 'delete-user <user_name>')."

        return output

    
    @staticmethod
    @_command
    def stop_server(server, args, kwargs) -> str:
        output = ""
        output += "Stopping the server..."
        
        server.stop()
        
        return output
    
    @staticmethod
    @_command
    def restart_server(server, args, kwargs) -> str:
        output = ""
        output += "Restarting the server..."
            
        server.stop()

        while server.is_running():
            sleep(0.1)

        sleep(0.5)

        #init_server()
        #Thread(target=run_server, daemon=True).start()
            
        return output

    def reload_config(server, args, kwargs) -> str:
        ...
    
    def get_config(server, args, kwargs) -> str:
        ...

    def set_config(server, args, kwargs) -> str:
        ...

        
            