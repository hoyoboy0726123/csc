import pytesseract
from PIL import Image
import cv2
import numpy as np

def extract_text_from_image(image_path):
    """
    Extract text from an image using OCR.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Extracted text from the image.
    """
    # Open the image file
    image = cv2.imread(image_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply binary threshold to segment out the text
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours of the text
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create a blank image for the extracted text
    extracted_text = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.uint8)

    # Iterate over the contours and extract the text
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        roi = gray[y:y+h, x:x+w]
        text = pytesseract.image_to_string(roi)
        cv2.rectangle(extracted_text, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(extracted_text, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)

    # Save the extracted text image
    cv2.imwrite('extracted_text.png', extracted_text)

    # Return the extracted text
    return pytesseract.image_to_string(image)

# Example usage
image_path = 'path_to_your_image.jpg'
extracted_text = extract_text_from_image(image_path)
print(extracted_text)
```

```python
import pytesseract
from PIL import Image
import cv2
import numpy as np

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file using OCR.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Extracted text from the PDF file.
    """
    # Open the PDF file
    image = cv2.imread(file_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply binary threshold to segment out the text
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours of the text
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create a blank image for the extracted text
    extracted_text = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.uint8)

    # Iterate over the contours and extract the text
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        roi = gray[y:y+h, x:x+w]
        text = pytesseract.image_to_string(roi)
        cv2.rectangle(extracted_text, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(extracted_text, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)

    # Save the extracted text image
    cv2.imwrite('extracted_text.png', extracted_text)

    # Return the extracted text
    return pytesseract.image_to_string(image)

# Example usage
file_path = 'path_to_your_pdf.pdf'
extracted_text = extract_text_from_pdf(file_path)
print(extracted_text)
```

```python
import pytesseract
from PIL import Image
import cv2
import numpy as np

def extract_text_from_html(html_string):
    """
    Extract text from an HTML string using OCR.

    Args:
        html_string (str): HTML string to extract text from.

    Returns:
        str: Extracted text from the HTML string.
    """
    # Convert the HTML string to an image
    image = cv2.imdecode(np.frombuffer(html_string.encode(), np.uint8), cv2.IMREAD_COLOR)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply binary threshold to segment out the text
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours of the text
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create a blank image for the extracted text
    extracted_text = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.uint8)

    # Iterate over the contours and extract the text
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        roi = gray[y:y+h, x:x+w]
        text = pytesseract.image_to_string(roi)
        cv2.rectangle(extracted_text, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(extracted_text, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)

    # Save the extracted text image
    cv2.imwrite('extracted_text.png', extracted_text)

    # Return the extracted text
    return pytesseract.image_to_string(image)

# Example usage
html_string = '<html><body>Hello World!</body></html>'
extracted_text = extract_text_from_html(html_string)
print(extracted_text)