"""Command handlers for the Twitch bot."""


def admin_required(func):
    """Decorator to mark a command handler method as requiring admin permissions.

    The CommandProcessor inspects this attribute at runtime to determine
    whether a command requires admin access, making the declaration explicit
    and co-located with the handler code. If you add a new admin command,
    just slap @admin_required on it — no separate list to maintain.
    """
    func._requires_admin = True
    return func
