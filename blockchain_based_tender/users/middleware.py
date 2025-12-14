from django.shortcuts import redirect

class MFAMiddleware:
    """Middleware to enforce MFA verification after password auth.

    If a logged-in user has `mfa_enabled` True and session does not
    have `mfa_verified`, redirect them to the MFA verification page.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for unauthenticated users
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            # Paths to exclude (so user can access setup/verify, logout, static, admin, etc.)
            excluded_paths = [
                '/mfa/verify/',
                '/mfa/setup/',
                '/mfa/disable/',
                '/api/mfa/verify/',
                '/api/mfa/setup/',
                '/api/mfa/disable/',
                '/logout/',
                '/accounts/logout/',
                '/accounts/login/',
                '/accounts/register/',
                '/accounts/password',
                '/admin/',
                '/static/',
            ]
            path = request.path
            if any(path.startswith(p) for p in excluded_paths):
                return self.get_response(request)

            # Enforce MFA for all authenticated users: if the session isn't
            # marked as verified, redirect to setup or verify depending on
            # whether the user has a stored TOTP secret.
            if not request.session.get('mfa_verified'):
                if not getattr(user, 'otp_secret', None):
                    return redirect('mfa_setup')
                return redirect('mfa_verify')

        return self.get_response(request)
