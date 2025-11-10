"""
Utility functions
"""
try:
    from slugify import slugify as python_slugify
    HAS_SLUGIFY = True
except ImportError:
    HAS_SLUGIFY = False
    import re


def generate_slug(text: str) -> str:
    """
    Generate URL-friendly slug from text
    Supports both latin and cyrillic (with transliteration)

    Examples:
        "My News Title" -> "my-news-title"
        "Моя новость" -> "moia-novost"
        "Hello World 123" -> "hello-world-123"
    """
    if HAS_SLUGIFY:
        return python_slugify(text)
    else:
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        return slug
