def leaderboard(args, kwargs) -> str:
    output = ""
    users = server.server_data.users.get()

    users = sorted(users, key=lambda player: player.get("stat_wins", 0), reverse=True)

    output = "Top users:\n"
    for user in users:
        output += f"{user['user_name']} - {user['stat_wins']}\n"
    
    return output

def test(args, kwargs) -> str:
    """
    Each custom command in plugins must implement a function with this signature: def ...(args, kwargs) -> str

    to call this command in any admin interface, enter 'test' and you can specify parameters, for example, 'test 0', 'test id=12 unmarked_test'.
    """
    print(f"Args: {args}")
    print(f"Kwargs: {kwargs}")

    # should always return a string, if None is returned it means an error occurred.
    return ""

def register(context) -> None:
    """
    Plugin registration function.

    Each plugin module must implement the register(context) -> None function.
    This function initializes the plugin and gets all the necessary objects and dependencies
    from the loader via the context dictionary.
    """
    global server, Log , User, server_data
    Log = context["Log"] 
    User = context["User"]
    server = context["server"]
    server_data = context["server_data"]