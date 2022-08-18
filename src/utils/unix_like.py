def unix_like() -> bool:
    import sys
    if 'win' in sys.platform:
        return False
    else:
        return True
