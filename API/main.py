import json
from flask import Flask, request, jsonify, send_file
import random
import string
import time
import os
import logging
import uuid

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
DATA_FILE = 'data.json'
def generate_usercode():
    return str(uuid.uuid4())[:8]


app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OBFUSCATE_FOLDER'] = 'obfuscator'

ADDITIONAL_CODE = """
local Players = game:GetService("Players")
local player = Players.LocalPlayer
local scriptid = "1234"
local scriptkey = "aIfx4kQN9z"
local hwid = game:GetService("RbxAnalyticsService"):GetClientId()
local ip = game:HttpGet("https://api64.ipify.org") 
local url = "api.lualist.adjumpnow.lol/execute"
local args = {
    "scriptid" = scriptid,
    "scriptkey" = scriptkey,
    "hwid" = hwid,
    "ip" = ip
}

local querystring = url.."?scriptid="..scriptid.."&scriptkey".."&hwid="..hwid.."&ip="..ip
local function makeRequest()
    local finalUrl = url..querystring

    local response
    local success, errorMessage = pcall(function()
        if syn and syn.request then
            response = syn.request({
                Url = finalUrl,
                Method = "GET"
            })
        elseif request then
            response = request({
                Url = finalUrl,
                Method = "GET"
            })
        elseif http and http.request then
            response = http.request({
                Url = finalUrl,
                Method = "GET"
            })
        else
            error("No supported HTTP request function found.")
        end
    end)

    if success and response then
        print("Request successful")
        print("Status Code: " .. response.StatusCode)
        print("Response Body: " .. response.Body)

        if response.StatusCode == 200 then
            local responseData = game:GetService("HttpService"):JSONDecode(response.Body)
            print("Response Data: ", responseData)
            lualistpremium()
        elseif response.StatusCode == 402 then
            player:Kick("Key not valid")
        elseif response.StatusCode == 400 then
            player:Kick("Error occurred with testing")
        elseif response.StatusCode == 401 then
            player:Kick("Key linked to different HWID, for using the script, use /resethwid")
        else
            player:Kick("An error has occurred")
        end
    else
        print("Error making the request: " .. (errorMessage or "Unknown error"))
        player:Kick("Request error: " .. (errorMessage or "Unknown error"))
    end
end

makeRequest()
"""

def convert_lua_to_function(lua_content):
    function_name = "lualistpremium"
    function_body = lua_content
    modified_lua_code = f"""
{ADDITIONAL_CODE}
function {function_name}()
{function_body}
end
"""
    return modified_lua_code

def generate_scriptkey(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def generate_apikey(length=25):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


def load_data():
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, 'r') as file:
        data = json.load(file)
    return data

def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)
    logging.debug("Data saved: %s", json.dumps(data, indent=4))

@app.route('/execute', methods=['GET'])
def execute_script():
    script_id = request.args.get('scriptid')
    script_key = request.args.get('scriptkey')
    hwid_header = request.args.get('hwid')
    ip = request.args.get('ip')

    logging.debug(f"script_id: {script_id}, script_key: {script_key}, hwid_header: {hwid_header}, ip: {ip}")

    if not script_id or not script_key or not hwid_header or not ip:
        return jsonify({'error': 'scriptid, scriptkey, hwid, and ip parameters are required'}), 400

    data = load_data()

    if not data:
        return jsonify({'error': 'data.json file not found'}), 500

    script_name = None
    script_executions = None
    for script in data.get("scripts", []):
        if script["id"] == script_id:
            script_name = script["name"]
            script_executions = script["executions"]
            break

    if script_name is None:
        return jsonify({'error': 'The provided scriptid does not exist'}), 404

    username = None
    hwid_user = None
    user_index = None

    for i, user in enumerate(data.get("users", [])):
        if user.get("script") == script_id and user.get("key") == script_key:
            username = user.get("userid")
            hwid_user = user.get("hwid")
            user['executions'] = user.get('executions', 0) + 1
            script["executions"] = script.get("executions", 0) + 1
            data['global'] = data.get('global', 0) + 1
            user_index = i
            break

    if username is None:
        return jsonify({'error': 'The provided scriptkey is not valid for this script'}), 402

    if hwid_user is None or hwid_user == hwid_header:
        data['users'][user_index]['hwid'] = hwid_header
        data['users'][user_index]['ip'] = ip  
        save_data(data)
        return jsonify({
            'script': script_name,
            'userid': username,
            'user_executions': data['users'][user_index]['executions'],
            'script_executions': script["executions"],
            'global_executions': data['global']
        }), 200
    else:
        return jsonify({'error': 'HwidMismatch'}), 401



@app.route('/whitelist', methods=['GET'])
def whitelist_user():
    guild_id = request.args.get('guildid')
    userid = request.args.get('userid')
    script_id = request.args.get('scriptid')
    author_id = request.args.get('authorid')

    if not guild_id or not userid or not script_id or not author_id:
        return jsonify({'error': 'guildid, userid, scriptid, and authorid parameters are required'}), 400

    data = load_data()

    if not data:
        return jsonify({'error': 'data.json file not found'}), 500

    script = next((script for script in data.get("scripts", []) if script["id"] == script_id and script["guildid"] == guild_id), None)
    if not script:
        return jsonify({'error': 'The provided guildid is not valid for the provided scriptid'}), 401

    if author_id not in script["owner"] and author_id not in script["contributors"]:
        return jsonify({'error': 'You are not authorized to whitelist users for this script'}), 403

    user = next((user for user in data.get("users", []) if user["userid"] == userid and user["script"] == script_id), None)
    if not user:
        new_user = {
            "userid": userid,
            "key": generate_scriptkey(),
            "script": script_id,
            "executions": 0,
            "hwid": None,
            "lrhwid": int(time.time()),
            "ips": []
        }
        data['users'].append(new_user)
        script["users"] = script.get("users", 0) + 1
        data['gbusers'] = data.get('gbusers', 0) + 1
        save_data(data)
        return jsonify({'message': 'User whitelisted', 'userid': userid}), 200

    return jsonify({'message': 'User already whitelisted', 'userid': userid}), 408

@app.route('/resethwid', methods=['POST'])
def reset_hwid():
    userid = request.args.get('userid')

    if not userid:
        return jsonify({'error': 'userid parameter is required'}), 400

    data = load_data()

    if not data:
        return jsonify({'error': 'data.json file not found'}), 500

    user_found = False
    current_time = int(time.time())

    for user in data.get("users", []):
        if user.get("userid") == userid:
            user_found = True
            lrhwid = user.get("lrhwid", 0)
            time_since_reset = current_time - lrhwid
            if time_since_reset >= 86400:
                user["hwid"] = None
                user["lrhwid"] = current_time
                save_data(data)  
                return jsonify({'message': 'Hwid reset successfully', 'userid': userid}), 200
            else:
                time_remaining = 86400 - time_since_reset
                return jsonify({'error': f'It has not been a day since the last reset. Time remaining: {time_remaining} seconds'}), 403
    
    if not user_found:
        return jsonify({'error': 'User not found'}), 404


@app.route('/create_and_obfuscate', methods=['POST'])
def create_and_obfuscate():
    owner_userid = request.form.get('owner_userid')
    script_name = request.form.get('name')
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not owner_userid or not script_name:
        return jsonify({'error': 'owner_userid and name parameters are required'}), 400

    filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + ".lua"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    file.save(file_path)
    
    with open(file_path, 'r') as f:
        original_code = f.read()
    
    combined_code = convert_lua_to_function(original_code)
    
    obfuscated_filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + ".lua"
    obfuscated_file_path = os.path.join(app.config['OBFUSCATE_FOLDER'], obfuscated_filename)
    
    with open(obfuscated_file_path, 'w') as archivo:
        archivo.write(combined_code)
    
    command = f"lua /obfuscate/cli.lua --preset Medium {obfuscated_file_path}"
    os.system(command)
    
    filename_without_extension = os.path.splitext(obfuscated_file_path)[0]
    final_obfuscated_file = f"{filename_without_extension}.obfuscate.lua"

    script_id = str(uuid.uuid4())
    apikey_final = generate_apikey()
    apikey = f"api_key_{apikey_final}"

    new_script = {
        "id": script_id,
        "name": script_name,
        "owner": owner_userid,
        "api_key": apikey,
        "guildid": None,
        "users": 0,
        "executions": 0,
        "contributors": []
    }

    data = load_data() or {"scripts": []}
    data['scripts'].append(new_script)
    save_data(data)

    response = {
        'message': 'Script created and code obfuscated',
        'script_id': script_id,
        'api_key': apikey,
    }

    return send_file(final_obfuscated_file, as_attachment=True), 200, {'Content-Disposition': f'attachment;filename={os.path.basename(final_obfuscated_file)}'}

@app.route('/force-resethwid', methods=['POST'])
def force_reset_hwid():
    userid = request.args.get('userid')

    if not userid:
        return jsonify({'error': 'userid parameter is required'}), 400

    data = load_data()

    if not data:
        return jsonify({'error': 'data.json file not found'}), 500

    user_found = False

    for user in data.get("users", []):
        if user.get("userid") == userid:
            user_found = True
            user["hwid"] = None
            user["lrhwid"] = int(time.time())
            save_data(data)  
            return jsonify({'message': 'Hwid reset successfully', 'userid': userid}), 200
    
    if not user_found:
        return jsonify({'error': 'User not found'}), 404





@app.route('/setup', methods=['POST'])
def setup_script():
    guild_id = request.args.get('guildid')
    api_key = request.args.get('api_key')

    if not guild_id or not api_key:
        return jsonify({'error': 'guildid and api_key arguments are required'}), 400

    data = load_data()

    if not data:
        return jsonify({'error': 'data.json file not found'}), 500

    scripts = data.get("scripts", [])
    script_found = False
    for script in scripts:
        if script.get("api_key") == api_key:
            script["guildid"] = guild_id
            script_found = True
            break
    
    if not script_found:
        return jsonify({'error': 'No script associated with the provided api_key'}), 404

    save_data(data)

    return jsonify({'message': 'guildid assigned to the script successfully'}), 200


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    userid = data.get('userid')

    if not username or not userid:
        return jsonify({'error': 'Missing username or userid'}), 400

    try:
        with open('data.json', 'r') as file:
            content = json.load(file)
    except FileNotFoundError:
        return jsonify({'error': 'data.json file not found'}), 500
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format'}), 500

    users_owners = content.get('users-owners', [])

    apikey = generate_apikey()
    usercode = generate_usercode()

    new_user = {
        'username': username,
        'userid': userid,
        'apikey': apikey,
        'usercode': usercode
    }
    users_owners.append(new_user)

    content['users-owners'] = users_owners
    try:
        with open('data.json', 'w') as file:
            json.dump(content, file, indent=4)
    except IOError:
        return jsonify({'error': 'Error writing to data.json'}), 500

    return jsonify({
        'username': username,
        'apikey': apikey,
        'usercode': usercode
    }), 200

@app.route('/create_script', methods=['POST'])
def create_script():
    owner_userid = request.args.get('owner_userid')
    script_name = request.args.get('name')

    if not owner_userid or not script_name:
        return jsonify({'error': 'owner_userid and name parameters are required'}), 400

    script_id = str(uuid.uuid4())

    apikey = generate_apikey()

    new_script = {
        "id": script_id,
        "name": script_name,
        "owner": owner_userid,
        "api_key": f"api_key_{apikey}",
        "guildid": None,
        "users": 0,
        "executions": 0,
        "contributors": []
    }

    data = load_data() or {"scripts": []}
    data['scripts'].append(new_script)
    save_data(data)

    return jsonify({'message': 'Script created', 'script_id': script_id}), 200

@app.route('/add_contributors', methods=['POST'])
def add_contributors():
    owner_userid = request.args.get('owner_userid')
    contributor_userid = request.args.get('contributor_userid')
    scriptid = request.args.get('scriptid')

    if not owner_userid or not contributor_userid or not scriptid:
        return jsonify({'error': 'owner_userid, contributor_userid, and scriptid parameters are required'}), 400

    data = load_data()

    if not data:
        return jsonify({'error': 'data.json file not found'}), 500

    script_found = False
    for script in data.get("scripts", []):
        if script["id"] == scriptid and script["owner"] == owner_userid:
            script_found = True
            if contributor_userid not in script["contributors"]:
                script["contributors"].append(contributor_userid)
                save_data(data)
                return jsonify({'message': 'Contributor added successfully'}), 200
            else:
                return jsonify({'error': 'Contributor already exists for this script'}), 409

    if not script_found:
        return jsonify({'error': 'No script found for the provided scriptid and owner_userid'}), 404

@app.route('/check_contributors', methods=['POST'])
def check_contributors():
    userid = request.args.get('userid')
    scriptid = request.args.get('scriptid')

    if not userid or not scriptid:
        return jsonify({'error': 'userid and scriptid parameters are required'}), 400

    data = load_data()

    if not data:
        return jsonify({'error': 'data.json file not found'}), 500

    script_found = False
    for script in data.get("scripts", []):
        if script["scriptid"] == scriptid:
            script_found = True
            if userid in script["contributors"] or script["owner"] == userid:
                return jsonify({'message': 'User is a contributor for this script'}), 200
            else:
                return jsonify({'message': 'User is not a contributor for this script'}), 403

    if not script_found:
        return jsonify({'error': 'No script found for the provided scriptid'}), 404



@app.route('/check_whitelisted', methods=['GET'])
def check_whitelisted():
    userid = request.args.get('userid')
    script_id = request.args.get('scriptid')

    if not userid or not script_id:
        return jsonify({'error': 'userid and scriptid parameters are required'}), 400

    data = load_data()

    if not data:
        return jsonify({'error': 'data.json file not found'}), 500

    for user in data.get("users", []):
        if user["userid"] == userid and user["script"] == script_id:
            return jsonify({'scriptkey': user.get("key", "")}), 200

    return jsonify({'error': 'User is not whitelisted for the provided script'}), 404

if __name__ == '__main__':
    app.run(port=5000)
