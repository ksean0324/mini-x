import unittest

import app


class GrokTest(unittest.TestCase):
    def setUp(self):
        self.context = app.app.test_request_context("/")
        self.context.push()

    def tearDown(self):
        self.context.pop()

    def test_answers(self):
        cases = [
            ("12*(3+4)", "84"),
            ("계산해줘 10 / 2", "5"),
            ("오늘 날짜 알려줘", "요일"),
            ("몇 시야?", "지금은"),
            ("날씨 알려줘", "실시간 날씨"),
            ("댓글은 어떻게 써?", "댓글 입력칸"),
        ]
        for question, expected in cases:
            with self.subTest(question=question):
                self.assertIn(expected, app.grok_answer(question))

    def test_question_is_html_escaped(self):
        client = app.app.test_client()
        response = client.post("/grok", data={"q": "<script>alert(1)</script>"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"<script>alert(1)</script>", response.data)


if __name__ == "__main__":
    unittest.main()
