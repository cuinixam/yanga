class UserNotificationException(Exception):
    """Exception raised to notify user about error detected.
    These are errors a user might be able to fix.
    This shall not be used to raise errors that are caused
    by the application missbehaviour.
    """

    pass
