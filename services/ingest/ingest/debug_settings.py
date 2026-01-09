from ingest.config import settings

def debug_settings():
    print(f"KIS_API_KEY: {settings.KIS_API_KEY is not None}")
    print(f"DART_API_KEY: {settings.DART_API_KEY is not None}")
    print(f"ECOS_API_KEY: {settings.ECOS_API_KEY}")
    print(f"DB_HOST: {settings.DB_HOST}")

if __name__ == "__main__":
    debug_settings()
