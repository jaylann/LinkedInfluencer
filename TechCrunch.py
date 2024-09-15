import requests
import html2text

# URL of the news article
url = "https://techcrunch.com/2024/09/13/a-fight-is-brewing-as-tusimple-tries-to-move-450m-to-china-and-pivot-from-self-driving-trucks-to-ai-animation/"

# Fetch the article content
response = requests.get(url)
html_content = response.text

# Convert HTML to plain text
text_maker = html2text.HTML2Text()
text_maker.ignore_links = True
article_text = text_maker.handle(html_content)

# Define markers for the extraction
start_marker = "#"
end_marker = "### More TechCrunch"

# Extract the text between the markers
def extract_text(text, start_marker, end_marker):
    # Find the start and end positions
    start_pos = text.find(start_marker)
    if start_pos == -1:
        return "Start marker not found."
    # Adjust to exclude the start marker
    start_pos += len(start_marker)

    # Find the end position
    end_pos = text.find(end_marker, start_pos)
    if end_pos == -1:
        return "End marker not found."

    # Extract and return the content
    return text[start_pos:end_pos].strip()

# Perform the extraction
extracted_text = extract_text(article_text, start_marker, end_marker)

# Output the extracted text
print(extracted_text)
