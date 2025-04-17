def get_client_ip(request):
    """Get the client IP address from the request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def log_user_action(request, action, details=None):
    """Log a user action to the database"""
    from .models import UserActionLog

    user_ip = get_client_ip(request)

    # Create the log entry
    log_entry = UserActionLog(action=action, user_ip=user_ip, details=details)
    log_entry.save()

    return log_entry
