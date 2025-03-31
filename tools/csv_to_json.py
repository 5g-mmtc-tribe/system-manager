#!/usr/bin/env python3
import csv
import json
import sys

def get_model(device_name):
    """Determine the model from the device name prefix."""
    if device_name.startswith("j10-"):
        return "Jetson-Nano"
    elif device_name.startswith("j20-"):
        return "Jetson-Xavier-NX"
    elif device_name.startswith("j40-"):
        return "Jetson-Orin-NX"
    else:
        return "Unknown"

def process_row(row):
    """
    Process a CSV row and return a dictionary with:
      - name: from device field
      - cable_id: for 6-column rows use col[1], for 7-column rows use col[2]
      - switch_interface: "GigabitEthernet" + (col[2] for 6-col rows, col[3] for 7-col rows)
      - nvidia_id: (col[3] for 6-col rows, col[4] for 7-col rows)
      - usb_instance: (col[4] for 6-col rows, col[5] for 7-col rows)
      - state: "Alive" if the notes field equals "available" (case‐insensitive), else "Dead"
    """
    # Determine if row has 6 or 7 columns.
    if len(row) == 6:
        name = row[0]
        cable_id = row[1]
        port = row[2]
        nvidia_id = row[3]
        usb_instance = row[4]
        notes = row[5]  # used to determine state
    elif len(row) == 7:
        name = row[0]
        # For rows with 7 columns the 2nd column (mac_addr) is ignored.
        cable_id = row[2]
        port = row[3]
        nvidia_id = row[4]
        usb_instance = row[5]
        notes = row[6]
    else:
        # if the row doesn't have the expected number of columns, skip it
        return None

    # Optionally skip rows without a USB instance
    if not usb_instance.strip():
        return None

    # Determine state: replace "available" with "Alive", otherwise "Dead"
    state = "Alive" if notes.strip().lower() == "available" else "Dead"

    # Build the JSON entry
    entry = {
        "name": name,
        "cable_id": cable_id,
        "switch_interface": f"GigabitEthernet{port}",
        "model": get_model(name),
        "nvidia_id": nvidia_id,
        "usb_instance": usb_instance,
        "state": state
    }
    return entry

def csv_to_json(csv_filename, json_filename):
    entries = []
    with open(csv_filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # skip header row
        for row in reader:
            processed = process_row(row)
            if processed:
                entries.append(processed)
                
    # (Optional) sort the entries in a custom order if needed.
    # For example, to sort by model then device name:
    # entries.sort(key=lambda x: (x["model"], x["name"]))

    with open(json_filename, "w") as jsonfile:
        json.dump(entries, jsonfile, indent=2)
    print(f"Converted {len(entries)} device entries into {json_filename}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python csv_to_json.py input.csv output.json")
        sys.exit(1)
    csv_filename = sys.argv[1]
    json_filename = sys.argv[2]
    csv_to_json(csv_filename, json_filename)
