# Placeholder cho Google OAuth2 custom (authlib/httpx-oauth), điền sau khi có
# GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET thật.
#
# Kế hoạch: dùng httpx-oauth.GoogleOAuth2 + fastapi_users.router.get_oauth_router(
#     oauth_client, auth_backend, settings.jwt_secret
# ), mount vào app/features/auth/router.py với prefix "/auth/google".
