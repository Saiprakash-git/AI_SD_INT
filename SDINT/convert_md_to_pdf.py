import markdown
from weasyprint import HTML
import sys

def convert_md_to_pdf(md_file, pdf_file):
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Convert markdown to html
        html_text = markdown.markdown(text, extensions=['extra'])
        
        # Add basic CSS for better looking PDF
        styled_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 2cm; }}
                h1, h2, h3 {{ color: #333; }}
                code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 4px; font-family: monospace; }}
                pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            {html_text}
        </body>
        </html>
        """
        
        HTML(string=styled_html).write_pdf(pdf_file)
        print(f"Successfully converted {md_file} to {pdf_file}")
    except Exception as e:
        print(f"Error converting {md_file}: {e}")

if __name__ == "__main__":
    convert_md_to_pdf('README.md', 'README.pdf')
    convert_md_to_pdf('DEVELOPMENT_TIMELINE.md', 'DEVELOPMENT_TIMELINE.pdf')
