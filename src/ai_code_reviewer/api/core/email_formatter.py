"""Email formatting utilities for converting review text to HTML."""

import re


def format_review_to_html(review_text: str) -> str:
    """Convert review text from markdown to HTML format for email"""
    # Convert markdown headers to HTML
    html_text = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", review_text, flags=re.MULTILINE)
    html_text = re.sub(r"^#### (.*?)$", r"<h4>\1</h4>", html_text, flags=re.MULTILINE)

    # Convert bold text
    html_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html_text)

    # Convert code blocks
    html_text = re.sub(r"```(\w*)\n(.*?)```", r'<pre><code class="\1">\2</code></pre>', html_text, flags=re.DOTALL)

    # Convert inline code
    html_text = re.sub(r"`([^`]+)`", r"<code>\1</code>", html_text)

    # Convert bullet points
    html_text = re.sub(r"^   - (.*?)$", r"   <li>\1</li>", html_text, flags=re.MULTILINE)

    # Convert newlines to <br> for better formatting
    html_text = html_text.replace("\n", "<br>\n")

    # Wrap in basic HTML structure
    return f"""
<html>
<body>
<div style="font-family: Arial, sans-serif; max-width: 800px;">
{html_text}
</div>
</body>
</html>
"""
