import pypandoc

def convert_to_docx(md_file, docx_file):
    try:
        # Convert markdown to docx using pandoc
        output = pypandoc.convert_file(md_file, 'docx', outputfile=docx_file)
        print(f"Successfully converted {md_file} to {docx_file}")
    except Exception as e:
        print(f"Error converting {md_file}: {e}")

if __name__ == "__main__":
    convert_to_docx('README.md', 'README.docx')
    convert_to_docx('DEVELOPMENT_TIMELINE.md', 'DEVELOPMENT_TIMELINE.docx')
