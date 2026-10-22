class MemoryCache:
    """ذاكرة تخزين مؤقت للتقليل من استعلامات قاعدة البيانات"""
    def __init__(self):
        self.cache = {}