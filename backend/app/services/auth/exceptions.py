class AuthenticationError(Exception):
    """
    Raised when authentication fails.
    """

    pass


class UserAlreadyExistsError(Exception):
    """
    Raised when attempting to create a user with an existing username.
    """

    pass
