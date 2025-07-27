class Color:
    reset = "\033[0m"
    
    red = "\033[31m"
    green = "\033[32m"
    blue = "\033[34m"
    aqua = "\033[96m"
    yellow = "\033[93m"
    gray = "\033[90m"

    def paint(message : str, color : str) -> str:
        """Returns a string colored in the specified color and closed with white."""
        return color + str(message) + Color.reset

if __name__ == '__main__':
    print("This is normal text")
    print(f"{Color.red}Now it is red!")
    print(f"{Color.green}Now it is green!")
    print(f"Still green... and reset ->{Color.reset}")
    print(f"text here {Color.paint('and colored text here', Color.aqua)} and text here")