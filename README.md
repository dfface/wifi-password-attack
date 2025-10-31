# WiFi Password Attack

I tried several attacks on different platforms, they are:

* Brute Force on macOS: `macos_brute_force.py`

All programs will maintain the progress, you can interrupt anytime.

## Usage

### macos_brute_force

You should download your password dictionary(like [this](https://github.com/danielmiessler/SecLists)) and get the WiFi Name(SSID), then run the program, like this:

```bash
python3 macos_brute_force.py -f ./dictionary/Chinese-common-password-list-top-1000000.txt -s TP-Link_ZYD6
```

run `python3 macos_brute_force.py -h` to get all options.
