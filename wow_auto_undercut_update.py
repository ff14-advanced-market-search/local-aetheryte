import os, json
from slpp import slpp as lua


# Specify the base directory and target Lua file name
base_directory = r"E:\World of Warcraft\_retail_\WTF\Account\12345678#2"

def read_and_parse_lua_file(file_path):
    """
    Read and parse a Lua file to a Python dictionary.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lua_data = file.read()

        # Remove the variable declaration if it's present to ensure proper parsing
        if 'UndercutJsonTable =' in lua_data:
            lua_data = lua_data.split('UndercutJsonTable =', 1)[1].strip()

        # Decode Lua table to Python dictionary
        raw_undercut_data = lua.decode(lua_data)
        # skip if no auctions found
        if len(raw_undercut_data) == 0:
            return

        undercut_data = []
        for _, value in raw_undercut_data.items():
            value['homeRealmName'] = str(value['homeRealmName'])
            undercut_data.append(value)

        return undercut_data
    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def update_region_undercut_json():
    # Find the Lua file
    lua_file_path = os.path.join(base_directory, "SavedVariables", "SaddlebagExchangeWoW.lua")

    # Check if the file was found and parse it
    if lua_file_path:
        print(f"Found Lua file at: {lua_file_path}")
        addonData = read_and_parse_lua_file(lua_file_path)

        # Convert dictionary to JSON formatted string and print it
        json_output = json.dumps(addonData, indent=4)
        print(json_output)

        # Define the output directory and file path
        output_dir = "wow_user_data/undercut"
        output_file = "region_undercut.json"
        output_path = os.path.join(output_dir, output_file)

        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Write JSON data to the file
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(json_output)
    else:
        print("Lua file not found.")


update_region_undercut_json()