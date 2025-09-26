import requests
from os import getenv
from pprint import pprint
from time import sleep

murl = 'https://api.mist.com/api/v1'
sesh = requests.Session()
sesh.headers = {"Authorization": f"Token {getenv('MIST_TOKEN')}", "Content-Type": "application/json"}
orgid = sesh.get(f"{murl}/self").json()['privileges'][0]['org_id']  # assumes only 1 item returned

def main():

    print("\nThis script will reset radios by creating and deleting a fake WLAN on the\n"
          "site(s) you select. This will cause a brief outage on the site(s) while the\n"
          "radios reset. It is useful to overcome issues such as when APs are not properly\n"
          "failing over to their backup RADIUS servers. Do not run this script if unless\n"
          "you fully understand the implications.\n")

    selection = input("What do you want to do?\n"
                      "1. Reset radios in a zone (EMEA, AMER)\n"
                      "2. Reset radios in a specific site\n"
                      "3. Exit\n"
                      "Enter your choice: ")
    if selection == '1':

        print("\nWARNING: This will reset radios in ALL sites in the zone you select. Zones are\n"
              "defined by the ZONE site variable.")

        reset_zone(input("Enter the zone (EMEA, AMER, etc.): ").strip().upper())

    elif selection == '2':
        site_id, name = Select_Site(get_sites())
        create_fake_wlan(site_id, name)

    sesh.close()


def Select_Site(sites):

    for index, site in enumerate(sites):
        print(f"{index}: {site['name']}")

    bad_input = True
    while bad_input:
        try:
            selection = int_catch("\nWhich site? ")
            siteid = sites[selection]['id']
            bad_input = False
        except IndexError:
            print("Bad input, try again.")

    print(f"Selected {sites[selection]['name']}")

    return siteid, sites[selection]['name']

def int_catch(promptstr):

    bad_input = True
    resp = ''
    while bad_input:
        try:
            resp = int(input(promptstr))
            bad_input = False
        except ValueError:
            print("Bad input, try again.")

    return resp


def reset_zone(zone):
    sites = get_sites()
    for site in sites:
        setting = sesh.get(f"{murl}/sites/{site['id']}/setting").json()

        try:
            if setting['vars']['ZONE'] == zone:
                create_fake_wlan(site['id'], site['name'])
        except KeyError:
            print(f"Skipping site {site['name']} as it does not have a ZONE variable set.")
            continue


def create_fake_wlan(site_id, name):
    print(f"Creating fake WLAN on site {name}")
    wlan = sesh.post(f"{murl}/sites/{site_id}/wlans", json=fakewlan).json()
    sleep(5)  # give Mist a moment to create the WLAN

    print(f"Deleting fake WLAN on site {name}")
    sesh.delete(f"{murl}/sites/{site_id}/wlans/{wlan['id']}")


def Name_Sort(dictionary):
    return dictionary['name']


def get_sites():
    url = f"{murl}/orgs/{orgid}/sites"

    sites_list = sesh.get(url).json()
    sites_list.sort(key=Name_Sort)

    return sites_list


fakewlan = {
    "ssid": "zz_radio_reset_ssid",
    "enabled": True,
    "auth": {
        "type": "open",
        "owe": "required"},
    "bands": ["24", "5", "6"]
}

if __name__ == "__main__":
    main()
