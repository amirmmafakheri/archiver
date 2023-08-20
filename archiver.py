import argparse
import requests
import re
import threading
import time

# Create an argument parser
parser = argparse.ArgumentParser(description="Send HTTP requests and print extracted words")

# Add the URL parameter argument
parser.add_argument("-u", "--url_param", required=True, help="The URL parameter to include in the request")

# Add the status code filter argument as a string
parser.add_argument("-fc", "--status_code_filter", default="200", help="The status code filter (comma-separated)")

# Add the output file argument
parser.add_argument("-o", "--output_file", help="Save the output to a file")

# Add the threading argument
parser.add_argument("-t", "--threads", type=int, default=1, help="Number of threads to use")

# Add the delay argument
parser.add_argument("-d", "--delay", type=float, default=0.0, help="Delay in seconds between requests")

# Parse the command-line arguments
args = parser.parse_args()

# Split the comma-separated status codes into a list
status_codes = args.status_code_filter.split(',')

# Define the file extensions in a variable
file_extensions = (
    '.3g2', '.3gp', '.7z', '.ai', '.aif', '.apk', '.arj', '.asp', '.aspx', '.avi', '.bak', '.bat', '.bin', '.bmp',
    '.c', '.cab', '.cda', '.cer', '.cfg', '.cfm', '.cgi', '.class', '.cpl', '.cpp', '.cs', '.css', '.csv', '.cur', '.dat',
    '.db', '.dbf', '.deb', '.dll', '.dmg', '.dmp', '.doc', '.docx', '.drv', '.email', '.eml', '.emlx', '.exe', '.flv',
    '.fnt', '.fon', '.gadget', '.gif', '.git', '.h', '.h264', '.hta', '.htm', '.html', '.icns', '.ico', '.inc', '.ini',
    '.iso', '.jar', '.java', '.jhtml', '.jpeg', '.jpg', '.js', '.jsa', '.jsp', '.key', '.lnk', '.log', '.m4v', '.mdb',
    '.mid', '.mkv', '.mov', '.mp3', '.mp4', '.mpa', '.mpeg', '.mpg', '.msg', '.msi', '.nsf', '.odp', '.ods', '.odt',
    '.oft', '.ogg', '.ost', '.otf', '.part', '.pcap', '.pdb', '.pdf', '.phar', '.php', '.php2', '.php3', '.php4', '.php5',
    '.php6', '.php7', '.phps', '.pht', '.phtml', '.pkg', '.pl', '.png', '.pps', '.ppt', '.pptx', '.ps', '.psd', '.pst',
    '.py', '.rar', '.reg', '.rm', '.rpm', '.rss', '.rtf', '.sav', '.sh', '.shtml', '.sql', '.svg', '.swf', '.swift',
    '.sys', '.tar', '.tar.gz', '.tex', '.tif', '.tiff', '.tmp', '.toast', '.ttf', '.txt', '.vb', '.vcd', '.vcf', '.vob',
    '.wav', '.wma', '.wmv', '.wpd', '.wpl', '.wsf', '.xhtml', '.xls', '.xlsm', '.xlsx', '.xml', '.z', '.zip'
)

# Create a set to store unique words
unique_words = set()

# Mutex for thread-safe access to the set
unique_words_lock = threading.Lock()

# Construct the complete URL with the status code filter
base_url = "https://web.archive.org/web/"

# Function to fetch and process data
def fetch_and_process(status_code):
    try:
        # Send an HTTP GET request to the original URL with the specified status code filter
        original_url = f"https://web.archive.org/cdx/search/cdx?url={args.url_param}&output=json&filter=statuscode:{status_code}&fl=timestamp&collapse=digest"
        response = requests.get(original_url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response to extract timestamps
            data = response.json()
            timestamps = [entry[0] for entry in data]

            # Loop through the timestamps and send requests to the generated URLs
            for timestamp in timestamps:
                if timestamp != 'timestamp':
                    timestamp_url = f"{base_url}{timestamp}if_/{args.url_param}"
                    response = requests.get(timestamp_url)
                    
                    # Extract words using regular expressions
                    # Include file extensions as part of words
                    extensions_pattern = "|".join(map(re.escape, file_extensions))
                    pattern = r'\b[\w-]+(?:' + extensions_pattern + r')?\b'
                    words = re.findall(pattern, response.text)
                    
                    # Add unique words to the set
                    with unique_words_lock:
                        unique_words.update(words)

                    # Introduce a delay between requests
                    time.sleep(args.delay)

        else:
            print(f"HTTP request failed with status code {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Create and start threads
threads = []
for _ in range(args.threads):
    for status_code in status_codes:
        thread = threading.Thread(target=fetch_and_process, args=(status_code,))
        threads.append(thread)
        thread.start()

# Wait for all threads to finish
for thread in threads:
    thread.join()

# Print unique words line by line or save to a file
if args.output_file:
    with open(args.output_file, 'w') as file:
        for word in unique_words:
            file.write(word + '\n')
else:
    for word in unique_words:
        print(word)
