# IDRISS AI Token Finder for Farcaster

## Getting Started

- Make sure you have Python 3.11.10
- Make sure you have Poetry installed

### Installation and Setup for Development

```shell
git clone https://github.com/victorpolisetty/idriss_project.git
cd visualisation_station
poetry env use 3.11.10
poetry install && poetry shell
make install
```

## How to run agent

```shell
./scripts/run_single_agent.sh victorpolisetty/idriss_frontend --force
```
Warning: Docker must be running

## How to run frontend (tested using Brave Browser)

```shell
http://localhost:5555/
```

## How to generate DB file

```shell
cd packages/victorpolisetty/customs/idriss_token_finder/database
python db_setup.db
```

## How to deploy

Setup Droplet on Digital Ocean:

1. Go to Digital Ocean

2. Click "Create Droplets"

3. Choose Region -> Default (San Francisco for me)

4. Choose Datacenter -> Default (San Francisco - Datacenter 3 - SF03)

5. VPC Network - Default

6. Choose an image -> Marketplace -> Search "Docker" -> Choose "Docker latest on Ubuntu 22.04"

7. Choose Size -> Basic

8. CPU options -> Regular Disk type: SSD + $6/mo

9. Choose Authentication Method => Password or SSH

10. Hostname -> Idriss Olas Token Finder

11. Create Droplet

## How to run inside Digital Ocean Droplet inside Console

Install System Updates:
```shell
sudo apt update && sudo apt upgrade -y
```

Install Required Dependencies
```shell
sudo apt install -y git curl build-essential
```

Install Python 3.11
```shell
#Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev
#Verify installation:
python3.11 --version  # Should output Python 3.11.x
```

Set Default Python to 3.10 (For System)
```shell
#Since APT & UFW require Python 3.10, set it as the default system version:
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 100
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 110
#Now explicitly CHOOSE Python 3.10 for system-wide use:
sudo update-alternatives --config python3
#Verify:
python3 --version  # Should output Python 3.10.x
```

Install Poetry
```shell
#Install Poetry for package management:
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="/root/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
#Verify Poetry installation:
poetry --version
```

Install Tendermint:
```shell
wget https://github.com/tendermint/tendermint/releases/download/v0.34.24/tendermint_0.34.24_linux_amd64.tar.gz
tar -xvf tendermint_0.34.24_linux_amd64.tar.gz
sudo mv tendermint /usr/local/bin/
tendermint version  # Verify installation
tendermint init --home /root/.tendermint
docker run -d --name tendermint \
  -p 26656:26656 \
  -p 26657:26657 \
  tendermint/tendermint start
```

Configure Nginx Reverse Proxy
```shell
#Install Nginx:
sudo apt install nginx -y
#Edit the Nginx config:
sudo vim /etc/nginx/sites-available/default
#Replace contents with:
server {
    listen 80;
    server_name YOUR_SERVER_IP;

    location / {
        proxy_pass http://127.0.0.1:5555;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
# You can get YOUR_SERVER_IP by running: curl ifconfig.me

#Restart Nginx:
sudo systemctl restart nginx
#Check if Nginx is running (should say active (running):
sudo systemctl status nginx
```

Set Up and Configure UFW Firewall
```shell
#Enable UFW:
sudo ufw enable
#Allow necessary ports:
sudo ufw allow 22/tcp     # SSH access
sudo ufw allow 80/tcp     # HTTP (if using a web service)
sudo ufw allow 443/tcp    # HTTPS (if using SSL)
sudo ufw allow 5555/tcp   # API service
#Reload UFW to apply changes:
sudo ufw reload
#Check firewall rules (make sure 5555 is ALLOW Anywhere:
sudo ufw status
```

Clone the Project Repository:
```shell
git clone https://github.com/victorpolisetty/idriss_project.git
cd idriss_project
```

Set Up the Virtual Environment with Poetry:
```shell
#Create a new Poetry environment with Python 3.11:
poetry env use python3.11
#Install project dependencies:
poetry install --no-root
#sync Olas packages
poetry run autonomy packages sync
#start docker tendermint
docker-compose up -d
```

Run the project
```shell
export OPENAI_API_KEY=YOUR_API_KEY
poetry run ./scripts/run_single_agent.sh victorpolisetty/idriss_frontend --force
```

Common Issues

- Tendermint not syncing
```shell
[2025-02-06 20:03:49,243][ERROR] [idriss_frontend] Could not synchronize with Tendermint!
[2025-02-06 20:03:49,244] [INFO] [idriss_frontend] Synchronizing with Tendermint...
```
Fix:
```shell
ps aux | grep tendermint
#Find process which is defunkt and kill it
sudo kill -9 <4 digit process number>
#Restart Tendermint
tendermint unsafe-reset-all --home /root/.tendermint
tendermint start --home /root/.tendermint &
```

## Commands

Here are common commands you might need while working with the project:

### Resetting Docker

```shell
curl localhost:8080/hard_reset
```

## When to use API's

Use the /api/analyze (POST) endpoint when a user is using natural language to search for a new coin.

Use the /api/wallet/{walletAddress} (GET) endpoint when we want to retain the users original query and just rescan for any updates.

## API Endpoints

- /api/analyze (POST)
  
  Request Body:
  JSON object as shown query and wallet_address required.
  
  ![Screenshot 2025-01-21 at 8 34 01 PM](https://github.com/user-attachments/assets/f6688ee8-7abf-4ed2-b0cb-cc44108206b5)

  Responses:
  
  200: Returns a string representing the results of the analysis with keys message, parameters, suggestion, first_ticker, results.

  message -> success message
  parameters -> parameters fed into the searchcaster API
  
  suggestion -> suggestion generated by GPT if it thinks more info could yield better results
  
  first_ticker -> ticker of the coin that best matches the prompt
  
  results -> the casts from farcaster analyzed
  
  400: Returns an error message when the request is malformed or missing required fields (e.g., missing query).

  ![Screenshot 2025-01-21 at 8 43 43 PM](https://github.com/user-attachments/assets/d2159bd8-3217-4185-b696-45a3e11151ab)

  ![Screenshot 2025-01-23 at 10 59 12 AM](https://github.com/user-attachments/assets/d2dc9b19-c598-43ad-a85e-51f15a97d53a)

  ![Screenshot 2025-01-23 at 1 59 01 PM](https://github.com/user-attachments/assets/9a211614-b97e-4709-ae0f-14d9cafcaf3b)

- /api/user/{walletAddress} (GET)
  
  Path Parameter:
  
  walletAddress (string, required) – The unique identifier for the user.
  
  Responses:
  
  200: Returns user information, including wallet address, engagement, text, and count.
  
  404: Returns an error message if the wallet address does not exist in the database.
  
  400: Returns an error message when the request is malformed.

  ![Screenshot 2025-01-21 at 8 38 25 PM](https://github.com/user-attachments/assets/f134974f-1bc7-4571-9499-19c1356672d4)

- /api/wallet/{walletAddress} (GET)

  Path Parameter:

  walletAddress (string, required) – The wallet address to check in the database.

  Responses:

  200: Returns SearchCaster API results along with associated parameters and the first ticker (e.g., $SOCIAL).
  
  404: Returns an error message if the wallet address is not found in the database.
  
  500: Returns an error message for any internal server errors.

  ![Screenshot 2025-01-21 at 8 41 54 PM](https://github.com/user-attachments/assets/874cc8ce-b937-4676-80b8-63afa4e62e16)

### Database Structure

Table Name: AnalyzeRequest

Table Columns:

wallet_address -> A unique wallet address which identifies the user STRING

count -> How many casts you want the SearchCaster API to search through INT

text -> What keywords you want the SearchCaster API to look for STRING

engagement -> What filters you want the SearchCaster API to sort by (one of: ["reactions","recasts","replies","watches"]) STRING

prompt -> Prompt that the user inputted STRING

![Screenshot 2025-01-23 at 1 33 49 PM](https://github.com/user-attachments/assets/a2c65f52-5dc7-4574-9b21-eb9bb02bc30f)

## License

This project is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

