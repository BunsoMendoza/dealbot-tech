import os
import tempfile
from utils import read_products


def test_read_products_minimal():
    csv = "title,url,price\nTest Product,https://example.com/p,19.99\n"
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(csv)
        prods, errs = read_products(path)
        assert len(prods) == 1
        assert not errs
        p = prods[0]
        assert p.title == "Test Product"
        assert p.url == "https://example.com/p"
        assert p.price == 19.99
    finally:
        os.remove(path)
