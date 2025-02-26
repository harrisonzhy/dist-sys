import matplotlib.pyplot as plt
import math

from utils import message as MSG
from client import Client

def construct_trace(size, client):
    message_content = ""
    for _ in range(size):
        message_content += "A"
    
    # Construct message using custom protocol
    args_custom = MSG.MessageArgs(message_content)
    message_custom = MSG.Message(message_args=args_custom, message_type="status", endpoint=client)

    # Construct message using JSON protocol
    args_json = MSG.MessageArgsJSON(message_content)
    message_json = MSG.Message(message_args=args_json, message_type="status", endpoint=client)

    len_content = len(message_content.encode())
    len_custom = len(message_custom.encode())
    len_json = len(message_json.encode())

    return len_content, len_custom, len_json

if __name__ == "__main__":
    original_sizes = []
    custom_sizes = []
    json_sizes = []

    client = Client()

    for size in range(1, 201):
        len_content, len_custom, len_json = construct_trace(size, client=client)
        original_sizes.append(len_content)
        custom_sizes.append(len_custom)
        json_sizes.append(len_json)

    # --- First Plot: Encoded sizes vs. raw content ---
    plt.figure(figsize=(8, 4))
    plt.plot(original_sizes, custom_sizes, label="Custom Protocol", color='blue', markersize=3, linestyle='-')
    plt.plot(original_sizes, json_sizes, label="JSON Protocol", color='green', markersize=3, linestyle='-')
    plt.xlabel("Encoded Raw Content (bytes)")
    plt.ylabel("Encoded Message Packet (bytes)")
    plt.title("Comparison of Custom vs. JSON Encoded Sizes (UTF-8)")
    plt.legend()
    plt.grid(True)
    plt.show()

    # --- Second Plot: Ratio of protocol bytes to raw content bytes ---
    ratio_custom = [ math.log(custom / raw) for custom, raw in zip(custom_sizes, original_sizes)]
    ratio_json = [ math.log(js / raw) for js, raw in zip(json_sizes, original_sizes)]

    plt.figure(figsize=(8, 4))
    plt.plot(original_sizes, ratio_custom, label="Custom-Raw Ratio", color='blue', markersize=3, linestyle='-')
    plt.plot(original_sizes, ratio_json, label="JSON-Raw Ratio", color='green', markersize=3, linestyle='-')
    plt.xlabel("Encoded Raw Content (bytes)")
    plt.ylabel("Log Protocol-Raw Ratio")
    plt.title("Log Ratio of Protocol Encoded Size to Raw Content Encoded Size (UTF-8)")
    plt.legend()
    plt.grid(True)
    plt.show()