import unittest
from pathlib import Path
from unittest.mock import patch

from report import render


class Report(unittest.TestCase):
    def test_untrusted_text_cannot_close_script(self):
        with patch.object(Path, "write_text") as save:
            path = Path("report.html")
            render(
                path,
                "Review",
                "Synthetic",
                {},
                [{"note": "</script><script>alert(1)</script>"}],
                "",
            )
            html = save.call_args.args[0]
            self.assertNotIn("</script><script>alert", html)
            self.assertIn(r"\u003c/script>", html)
            self.assertIn("<p>Synthetic</p>", html)


if __name__ == "__main__":
    unittest.main()
