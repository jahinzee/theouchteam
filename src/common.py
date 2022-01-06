"""
The OUCH Team
Common boring modules to simplify life :)
"""

class common:
    def isInt(x):
        try:
            int(x)
            return True
        except ValueError:
            return False