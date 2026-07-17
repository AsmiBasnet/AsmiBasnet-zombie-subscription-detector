import zipfile
import xml.etree.ElementTree as ET
import os

def extract_docx_text(docx_path):
    """
    Extracts text from a .docx file using standard library zipfile and xml parser.
    """
    if not os.path.exists(docx_path):
        print(f"Error: {docx_path} does not exist.")
        return None
        
    try:
        # A docx file is actually a zip archive containing XML files
        with zipfile.ZipFile(docx_path) as docx:
            # The main text content is stored in word/document.xml
            xml_content = docx.read('word/document.xml')
            
        # Parse the XML structure
        root = ET.fromstring(xml_content)
        
        # Word XML namespaces
        ns = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
        
        paragraphs = []
        # Find all paragraph elements
        for paragraph in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = []
            # Find all text elements within the paragraph
            for text_elem in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                if text_elem.text:
                    texts.append(text_elem.text)
            
            # Combine the text fragments in this paragraph
            p_text = "".join(texts)
            paragraphs.append(p_text)
            
        return "\n\n".join(paragraphs)
        
    except Exception as e:
        print(f"An error occurred while reading the docx file: {e}")
        return None

def main():
    docx_file = "Zombie_Subscription_Detector_PID.docx"
    output_file = "Zombie_Subscription_Detector_PID.md"
    
    print(f"Reading '{docx_file}'...")
    text_content = extract_docx_text(docx_file)
    
    if text_content is not None:
        # Write to a Markdown file so it is easy to read
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        print(f"Successfully extracted text to '{output_file}'!")
    else:
        print("Failed to extract text.")

if __name__ == "__main__":
    main()
