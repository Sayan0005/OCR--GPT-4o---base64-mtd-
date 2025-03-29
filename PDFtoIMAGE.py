from pdf2image import convert_from_path

# Convert PDF pages to images at 300 DPI for better quality
pages = convert_from_path('sample-tables.pdf', dpi=300)

# Save each page as a PNG file
for i, page in enumerate(pages):
    page.save(f'page_{i + 1}.png', 'PNG')
