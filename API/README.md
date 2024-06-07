Certainly! Below is the documentation for the provided code, translated into English:

---

### Luau Script Management API

This Flask application provides an API for managing scripts and whitelisted users.

#### Endpoints:

1. **Execute Script**
   - Endpoint: `/execute`
   - Method: `GET`
   - Parameters:
     - `scriptid`: ID of the script to execute.
     - `scriptkey`: Key for accessing the script.
     - `hwid`: Hardware ID of the user.
     - `ip`: IP address of the user.
   - Description: Executes a script for the provided user if the script ID and key are valid, and the hardware ID matches. Returns information about the execution.

2. **Whitelist User**
   - Endpoint: `/whitelist`
   - Method: `GET`
   - Parameters:
     - `guildid`: ID of the guild.
     - `userid`: ID of the user to whitelist.
     - `scriptid`: ID of the script to whitelist the user for.
     - `authorid`: ID of the authorizing user.
   - Description: Whitelists a user for a specific script in a guild. Only authorized users can perform this action.

3. **Reset HWID**
   - Endpoint: `/resethwid`
   - Method: `POST`
   - Parameters:
     - `userid`: ID of the user to reset the HWID for.
   - Description: Resets the Hardware ID (HWID) of a user after a day has passed since the last reset.

4. **Force Reset HWID**
   - Endpoint: `/force-resethwid`
   - Method: `POST`
   - Parameters:
     - `userid`: ID of the user to force reset the HWID for.
   - Description: Forces the reset of the Hardware ID (HWID) of a user.

5. **Setup Script**
   - Endpoint: `/setup`
   - Method: `POST`
   - Parameters:
     - `guildid`: ID of the guild.
     - `api_key`: API key associated with the script.
   - Description: Associates a guild ID with a script using the provided API key.

6. **Create Script**
   - Endpoint: `/create_script`
   - Method: `POST`
   - Parameters:
     - `owner_userid`: ID of the owner user.
     - `name`: Name of the script to create.
   - Description: Creates a new script with a unique ID and generates an API key.

7. **Add Contributors**
   - Endpoint: `/add_contributors`
   - Method: `POST`
   - Parameters:
     - `owner_userid`: ID of the owner user.
     - `contributor_userid`: ID of the contributor user to add.
   - Description: Adds a contributor to a script, if the owner authorizes it.

8. **Check Contributors**
   - Endpoint: `/check_contributors`
   - Method: `POST`
   - Parameters:
     - `userid`: ID of the user to check.
     - `scriptid`: ID of the script to check for contributors.
   - Description: Checks if a user is a contributor for a specific script.

9. **Check Whitelisted**
   - Endpoint: `/check_whitelisted`
   - Method: `GET`
   - Parameters:
     - `userid`: ID of the user to check.
     - `scriptid`: ID of the script to check if the user is whitelisted.
   - Description: Checks if a user is whitelisted for a specific script.

#### Data Storage:

- The application uses a JSON file (`data.json`) to store script and user information.
- Data is loaded and saved using helper functions (`load_data` and `save_data`).

---

This Flask application provides a comprehensive API for managing scripts and whitelisted users, enabling various operations such as script execution, whitelisting users, resetting HWIDs, setting up scripts, and more.