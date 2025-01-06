# dyndns_porkbun
Simple DynDNS script for use with Porkbun

## Usage
Create an API key and secret in the Porkbun web interface.  Then set the following environment variables:

```
export PORKBUN_API_KEY=your_api_key
export PORKBUN_SECRET=your_secret
```
then run the script with the domain and subdomain you want to update:

```
./dyndns_porkbun.py example.com subdomain
```

It will look up the current external IP address from your host and update the DNS record if it has changed.

## Systemd example

First put the environment variables in a config file `/etc/syndns.conf`:
```
PORKBUN_API_KEY=your_api_key
PORKBUN_SECRET=your_secret
```
and make sure this file is readable by the group `dyndns` and no one else.

Then create a systemd service file in `/etc/systemd/system/dyndns_porkbun.service`:

```systemd
[Unit]
Description=DynDNS updates
After=network-online.target

[Service]
DynamicUser=true
SupplementaryGroups=dyndns
Type=oneshot
EnvironmentFile=/etc/dyndns.conf
ExecStart=/usr/local/bin/dyndns_porkbun.py example.net hostname

[Install]
WantedBy=multi-user.target
```

and a timer file to run it every hour or so in `/etc/systemd/system/dyndns_porkbun.timer`:

```systemd
[Unit]
Description=Run dyndns_porkbun every hour

[Timer]
OnCalendar=*-*-* *:0:0
Persistent=true

[Install]
WantedBy=multi-user.target
```

Then enable and start the timer:

```
systemctl enable dyndns_porkbun.timer
systemctl start dyndns_porkbun.timer
```
