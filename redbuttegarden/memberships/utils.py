class SafeFormatDict(dict):
    def __missing__(self, key):
        return ""
