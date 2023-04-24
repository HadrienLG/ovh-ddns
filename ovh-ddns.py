import json
import ovh
from requests import get
import logging

# Fichier de paramètres
data_file_path = "/usr/local/sbin/ovh-ddns.json"

# Fichier de journalisation
logging.basicConfig(handlers=[logging.FileHandler(filename="/var/log/ovh-ddns.log", 
                                                 encoding='utf-8', mode='a+')],
                    format="%(asctime)s %(name)s:%(levelname)s:%(message)s", 
                    datefmt="%F %A %T", 
                    level=logging.INFO)

## Updates the OVH DNS record value to be the new public IP address of the server
def update_ovh(data):
    logging.info('Mise à jour des informations du compte OVH')
    try:
        client = ovh.Client(
            endpoint            = data["ovh_endpoint"],
            application_key     = data["ovh_application_key"],
            application_secret  = data["ovh_application_secret"],
            consumer_key        = data["ovh_consumer_key"]
        )

        client.put(
            "/domain/zone/{}/record/{}".format(
                data["dns_zone_name"],
                data["dns_record_id"]
            ),
            subDomain   = data["dns_record_subdomain"],
            target      = data["dns_record_target"],
            ttl         = data["dns_record_ttl"]
        )
    except Exception as e:
        logging.warn("Unable to update OVH DNS record")
        logging.info("Try running setup.sh again")
        logging.debug(e)
        return
    
    update_local_data_store(data)


## Updates the local ovh-ddns.json file to contain the new public IP address
def update_local_data_store(data):
    logging.info('Mise à jour des données locales')
    try:
        file = open(data_file_path, "w")
    except:
        print("Unable to locate ovh-ddns.json")
    else:
        data["first_time"] = False

        try:
            file.write(json.dumps(data))
            file.close()
            print("Updated old IP")
        except Exception as e:
            print(e)


## Reads ovh-ddns.json file and gets current public IP
## address and compares the two to check for a change
def main():
    logging.debug('Execution du script principal')
    old_ip = ""

    try:
        # Chargement des données locales
        logging.debug('Chargement des données locales...')
        file = open(data_file_path, "r")
        data = json.loads(file.read())
        file.close()
        logging.debug('...chargement des données locales effectué')
        old_ip = data["ip"]
    except FileNotFoundError:
        logging.warn('Echec du chargement des données locales')
        print("Data file not found. Run the setup.sh script first.")
    else:
        # Poursuite du script avec la mise à jour de l'adresse IP si nécessaire
        try:
            # API ipify.org
            res = get("https://api.ipify.org")
            if res.status_code == 200:
                current_ip = res.text
                logging.info(f'Adresse IP courante {current_ip} depuis IPIFY.org')
            else:
                logging.warn(f'Erreur lors obtention IP depuis depuis IPIFY.org')
                # API ipapi.co
                res = get('https://ipapi.co/json/')
                if res.status_code == 200:
                    current_ip = res.json()['ip']
                    logging.info(f'Adresse IP courante {current_ip} depuis IPAPI.co')
                else:
                    logging.warn(f'Erreur lors obtention IP depuis depuis IPAPI.org')

            if current_ip != old_ip:
                logging.info("IP change detected")
                data["ip"] = current_ip
                update_ovh(data)
                logging.debug("Adresse IP mise à jour")
            elif data["first_time"]:
                logging.debug("First time run")
                update_ovh(data)
            else:
                logging.info(f"No IP change detected, IP is {current_ip}")

        except:
            logging.warn("Unable to retrieve public IP address")


if __name__ == "__main__":
    main()
