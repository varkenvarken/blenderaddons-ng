import sys
from pathlib import Path
from bs4 import BeautifulSoup

def swap_head(html_file: str, template_file: str) -> None:
    """Replace the <head> element in an HTML file with contents from a template file."""
    
    html_path = Path(html_file)
    template_path = Path(template_file)
    
    if not html_path.exists():
        print(f"Error: HTML file not found: {html_file}")
        sys.exit(1)
    
    if not template_path.exists():
        print(f"Error: Template file not found: {template_file}")
        sys.exit(1)
    
    # Read the HTML file
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Read the template file
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Parse the template
    template_soup = BeautifulSoup(template_content, 'html.parser')
    template_head = template_soup.find('head')
    
    if not template_head:
        print("Error: No <head> element found in template file")
        sys.exit(1)
    
    # Find and replace the head element
    existing_head = soup.find('head')
    if existing_head:
        existing_head.replace_with(template_head)
    else:
        # If no head exists, insert it at the beginning
        html_tag = soup.find('html')
        if html_tag:
            html_tag.insert(0, template_head)
        else:
            print("Error: No <html> element found in HTML file")
            sys.exit(1)
    
    # Write the modified HTML back
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()))
    
    print(f"Successfully updated {html_file}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python headswap.py <html_file> <template_file>")
        sys.exit(1)
    
    swap_head(sys.argv[1], sys.argv[2])