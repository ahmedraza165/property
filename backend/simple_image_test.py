#!/usr/bin/env python3
"""Simple test to show images and prompts"""

import csv

# Read first property from CSV
csv_path = "Export_Contacts_Cleaned Target Best Lehigh_Dec_2025_5_41_PM.csv"

with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    properties = list(reader)

# Get first property
prop = properties[0]

print("="*80)
print("TEST PROPERTY DATA")
print("="*80)
print(f"Name: {prop['Name']}")
print(f"Address: {prop['Street address']}")
print(f"City: {prop['City']}")
print(f"State: {prop['State']}")
print(f"Postal Code: {prop['Postal Code']}")
print(f"Full Address: {prop['Street address']}, {prop['City']}, {prop['State']} {prop['Postal Code']}")
