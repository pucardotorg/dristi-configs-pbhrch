import requests
import csv
import logging
import argparse

# Environment URL mapping
ENV_URLS = {
    "dev": "https://dristi-kerala-dev.pucar.org",
    "qa": "https://dristi-kerala-qa.pucar.org",
    "demo": "https://demo.pucar.org",
    "prod": "https://oncourts.kerala.gov.in",
}
LOCALIZATION_SEARCH_API = "/localization/messages/v1/_search?&tenantId={tenant_id}&locale="

# Neglect lists if you want to neglect code or by module add in below arrays
NEGLECT_CODES = ["MOBILE_VIEW_ERROR ", "MOVE_CASE_OUT_OF_LONG_PENDING_REGISTER ", "MOVE_CASE_TO_LONG_PENDING_REGISTER ","JUDGEMENT_NOT_ALLOWED_FOR_LPR_CASE","Close", "Review Process", "SEARCH_CASE_NAME_OR_NUMBER", "Code",]
NEGLECT_MODULES = []

# Supported locales
LOCALES = ["en_IN"] #, "ml_IN"]

# Headers for API requests
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer ed8499ca-58dc-404e-b5ec-4fa2d88a69ec",
}

# Payload structure
payload = {
    "RequestInfo": {
        "apiId": "Rainmaker",
        "msgId": "1716217310250|locale",
        "plainAccessRequest": {},
    }
}

# Logger setup for better error handling and debugging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_localization_data(url, locale, tenant_id):
    """
    Fetches localization data from the given URL and locale.

    :param url: API URL to fetch localization data from
    :param locale: Locale to fetch data for
    :param tenant_id: Tenant ID to use in the API request
    :return: JSON response containing localization messages
    """
    try:
        payload["RequestInfo"]["msgId"] = f"1716217310250|{locale}"
        response = requests.post(
            url + LOCALIZATION_SEARCH_API.format(tenant_id=tenant_id) + locale,
            json=payload,
            headers=HEADERS,
            verify=False,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(
            f"Error fetching localization for URL: {url}, Locale: {locale}. Error: {e}"
        )
        return None


def compare_localization(source_localization, target_localization, locale):
    """
    Compares source localization data with target localization data.

    :param source_localization: Source localization messages
    :param target_localization: Target localization messages
    :param locale: Locale being compared
    :return: List of missing codes and a count of matched codes
    """
    missing_codes = []

    for code in source_localization:
        if (
            code not in target_localization
            and code["code"] not in NEGLECT_CODES
            and code["module"] not in NEGLECT_MODULES
        ):
            missing_codes.append((code["code"], code["message"], code["module"]))

    return missing_codes


def save_missing_localizations(missing_codes, locale):
    """
    Saves the missing localization codes to a CSV file.

    :param missing_codes: List of tuples containing missing localization codes
    :param locale: Locale for which the missing translations are saved
    """
    try:
        file_name = f"missing_translations_in_{locale}.csv"
        with open(file_name, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Code", "Message", "Module"])
            writer.writerows(missing_codes)
        logging.info(f"CSV file created with missing translations for locale: {locale}")
    except Exception as e:
        logging.error(f"Error saving missing translations for locale {locale}: {e}")


def process_localizations(locale):
    """
    Main function to process localization comparison and saving missing translations.

    :param locale: Locale to process
    """
    try:
        logging.info(f"Comparing localization for locale: {locale}")

        source_response = get_localization_data(SOURCE_URL, locale, SOURCE_TENANT_ID)
        target_response = get_localization_data(TARGET_URL, locale, TARGET_TENANT_ID)

        # Ensure both source and target responses are not None
        if source_response and target_response:
            source_localization = source_response.get("messages", [])
            target_localization = target_response.get("messages", [])

            # Compare the localization data
            missing_codes = compare_localization(
                source_localization, target_localization, locale
            )

            # Save missing codes to CSV
            save_missing_localizations(missing_codes, locale)

            # Log the results
            logging.info(
                f"Locale: {locale}, Source count: {len(source_localization)}, Target count: {len(target_localization)}, Mismatched: {len(missing_codes)}"
            )
        else:
            logging.error(
                f"Localization data missing for either source or target for locale: {locale}"
            )

    except Exception as e:
        logging.error(f"Error processing localization for locale {locale}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare localization between two environments")
    parser.add_argument("--source", required=True, choices=ENV_URLS.keys(), help="Source environment (dev, qa, demo, prod)")
    parser.add_argument("--target", required=True, choices=ENV_URLS.keys(), help="Target environment (dev, qa, demo, prod)")
    parser.add_argument("--source-tenant", default="pb", help="Tenant ID for source environment (default: pb)")
    parser.add_argument("--target-tenant", default="pb", help="Tenant ID for target environment (default: pb)")
    args = parser.parse_args()

    SOURCE_URL = ENV_URLS[args.source]
    TARGET_URL = ENV_URLS[args.target]
    SOURCE_TENANT_ID = args.source_tenant
    TARGET_TENANT_ID = args.target_tenant

    logging.info(f"Source: {args.source} ({SOURCE_URL}), TenantId: {SOURCE_TENANT_ID}")
    logging.info(f"Target: {args.target} ({TARGET_URL}), TenantId: {TARGET_TENANT_ID}")

    for locale in LOCALES:
        process_localizations(locale)
