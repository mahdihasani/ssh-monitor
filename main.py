
# Import required modules
import subprocess
import os
import time
from datetime import datetime
import re
import requests

# Check if logs file is enabled
with open("/etc/ssh/sshd_config", "r") as sc:
    sc_lines = sc.read().split("\n")
    sc_conf = []
    for item in sc_lines:
        if not item.startswith("#"):
            sc_conf.append(item)

    if "LogLevel INFO" in sc_conf:
        print("ssh configure for logs")
    else:
        print("configure ssh for enable logging")
        with open("/etc/ssh/sshd_config", "a") as nesc:
            nesc.write("#this data was added with onroute firewall\n")
            nesc.write("SyslogFacility AUTH\nLogLevel INFO\n")
            subprocess.Popen(["service","ssh","restart"])
            subprocess.Popen(["service","sshd","restart"])

# Function to get the last file change timestamp
def get_last_file_change(file_path):
    try:
        # Get the file's metadata
        file_stat = os.stat(file_path)
        # Retrieve the timestamp of the last modification
        last_change_timestamp = file_stat.st_mtime
        # Convert the timestamp to a readable format
        return last_change_timestamp
    except FileNotFoundError:
        print("File not found.")
        return None

log_path = "/var/log/auth.log"  # Replace with the actual file path

# Function to send a message via Bale messenger
def send_bale(result):
    token = os.environ.get("bale_token")
    user_id = int(os.environ.get("user_id"))
    r = requests.post(f"https://tapi.bale.ai/bot{token}/sendMessage",
                      params={"chat_id": user_id, "text": result})

# Function to read the file from the end based on a stop time
def read_file_from_end(file_path, stop_time):
    with open(file_path, "rb") as file:
        file_size = os.stat(file_path).st_size
        lines = []
        lines_count = 0
        chunk_size = 1024  # Adjust the chunk size as needed

        # Read the file in chunks from the end
        for i in range(file_size // chunk_size, -1, -1):
            file.seek(i * chunk_size)
            chunk = file.read(chunk_size).decode()
            # Reverse the chunk to start processing from the end
            chunk = chunk[::-1]
            end = False
            # Process the chunk line by line
            for line in chunk.splitlines():
                if end:
                    break
                data = line[::-1]
                pattern = r"(\w{3} \d{2} \d{2}:\d{2}:\d{2})"
                match = re.search(pattern, data)
                if match:
                    datetime_str = match.group(1)
                    now = datetime.now()
                    datetime_timestamp = datetime.strptime(str(now.year) + " " + datetime_str, "%Y %b %d %H:%M:%S")
                    datetime_timestamp = int(datetime_timestamp.timestamp())
                    if datetime_timestamp <= stop_time:
                        end = True
                        break
                    else:
                        lines.append(line[::-1])

        # Reverse the lines to restore the original order
        lines.reverse()

        # Print or process the lines as needed
        for line in lines:
            checkout_data = line.split(" ")[3:]
            result = ""
            for i in checkout_data:
                result += i + " "
            send_bale(result)

# Set the initial check time
last_change = int(datetime.now().timestamp())
send_bale("service was started")
while True:
    new_change = get_last_file_change(log_path)
    if new_change != last_change:
        read_file_from_end(log_path, last_change)
        last_change = int(new_change)
    else:
        time.sleep(1)
