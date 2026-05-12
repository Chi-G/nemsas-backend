import json
import os
from collections import defaultdict

def find_duplicates():
    json_path = os.path.join(os.path.dirname(__file__), "users.json")
    output_path = os.path.join(os.path.dirname(__file__), "duplicate_users.json")
    
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return

    with open(json_path, 'r') as f:
        users = json.load(f)

    # Group users by email
    email_groups = defaultdict(list)
    for u in users:
        email = u.get("email")
        if email:
            email_groups[email].append(u)

    # Find groups with more than 1 user
    duplicates = []
    for email, group in email_groups.items():
        if len(group) > 1:
            duplicates.extend(group)

    # Save to file
    with open(output_path, 'w') as f:
        json.dump(duplicates, f, indent=4)

    print(f"🔍 Found {len(duplicates)} records sharing {len([e for e, g in email_groups.items() if len(g) > 1])} duplicate emails.")
    print(f"📂 Saved duplicate records to: {output_path}")

if __name__ == "__main__":
    find_duplicates()
