import os


def load_system_role_for_timestamped_translation():
    role_file = "system_role_for_timestamped_translation_2.txt"
    if not os.path.exists(role_file):
        raise FileNotFoundError(f"System role file '{role_file}' not found.")

    with open(role_file, "r", encoding="utf-8") as f:
        return f.read().strip()