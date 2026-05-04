import os
import csv
import logging
import requests
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ENV_URLS = {
    "dev":  f"https://{os.getenv('DEV_URL',  'dristi-kerala-dev.pucar.org')}",
    "qa":   f"https://{os.getenv('QA_URL',   'dristi-kerala-qa.pucar.org')}",
    "demo": f"https://{os.getenv('DEMO_URL', 'demo.pucar.org')}",
    "prod": f"https://{os.getenv('PROD_URL', 'oncourts.kerala.gov.in')}",
}

VALID_ENVS = list(ENV_URLS.keys())

LOCALIZATION_SEARCH_PATH = "/localization/messages/v1/_search"
LOCALIZATION_UPSERT_PATH = "/localization/messages/v1/_upsert"

NEGLECT_CODES = {
    "MOBILE_VIEW_ERROR ",
    "MOVE_CASE_OUT_OF_LONG_PENDING_REGISTER ",
    "MOVE_CASE_TO_LONG_PENDING_REGISTER ",
    "JUDGEMENT_NOT_ALLOWED_FOR_LPR_CASE",
    "Close",
    "Review Process",
    "SEARCH_CASE_NAME_OR_NUMBER",
    "Code",
}
NEGLECT_MODULES: set = set()


@dataclass
class MissingTranslation:
    code: str
    message: str
    module: str


@dataclass
class ComparisonResult:
    source_env: str
    target_env: str
    source_count: int
    target_count: int
    missing: List[MissingTranslation] = field(default_factory=list)
    csv_path: Optional[str] = None
    error: Optional[str] = None

    @property
    def missing_count(self) -> int:
        return len(self.missing)

    def by_module(self) -> Dict[str, List[MissingTranslation]]:
        result: Dict[str, List[MissingTranslation]] = {}
        for t in self.missing:
            result.setdefault(t.module, []).append(t)
        return result


@dataclass
class UpdateResult:
    target_env: str
    total_processed: int
    total_skipped: int
    total_upserted: int
    failed_code: Optional[str] = None
    error: Optional[str] = None


def _search_headers() -> dict:
    token = os.getenv("LOCALIZATION_BEARER_TOKEN", "")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def _env_creds(env: str) -> dict:
    prefix = env.upper()
    return {
        "url": os.getenv(f"{prefix}_URL", ""),
        "username": os.getenv(f"{prefix}_USERNAME", ""),
        "password": os.getenv(f"{prefix}_PASSWORD", ""),
    }


def fetch_localization_messages(
    env: str, tenant_id: str = "pb", locale: str = "en_IN"
) -> Optional[List[dict]]:
    url = ENV_URLS.get(env)
    if not url:
        logging.error(f"Unknown environment: {env}")
        return None
    api_url = f"{url}{LOCALIZATION_SEARCH_PATH}?&tenantId={tenant_id}&locale={locale}"
    payload = {
        "RequestInfo": {
            "apiId": "Rainmaker",
            "msgId": f"1716217310250|{locale}",
            "plainAccessRequest": {},
        }
    }
    try:
        resp = requests.post(
            api_url, json=payload, headers=_search_headers(), verify=False, timeout=30
        )
        resp.raise_for_status()
        return resp.json().get("messages", [])
    except Exception as e:
        logging.error(f"fetch_localization_messages failed for {env}: {e}")
        return None


def compare_envs(
    source: str,
    target: str,
    source_tenant: str = "pb",
    target_tenant: str = "pb",
    locale: str = "en_IN",
    save_csv: bool = True,
    csv_dir: str = ".",
) -> ComparisonResult:
    source_msgs = fetch_localization_messages(source, source_tenant, locale)
    target_msgs = fetch_localization_messages(target, target_tenant, locale)

    if source_msgs is None or target_msgs is None:
        return ComparisonResult(
            source_env=source,
            target_env=target,
            source_count=0,
            target_count=0,
            error="Failed to fetch data from one or both environments",
        )

    target_codes = {m["code"] for m in target_msgs}
    missing: List[MissingTranslation] = []

    for msg in source_msgs:
        code = msg.get("code", "")
        module = msg.get("module", "")
        if (
            code not in target_codes
            and code not in NEGLECT_CODES
            and module not in NEGLECT_MODULES
        ):
            missing.append(
                MissingTranslation(
                    code=code,
                    message=msg.get("message", ""),
                    module=module,
                )
            )

    result = ComparisonResult(
        source_env=source,
        target_env=target,
        source_count=len(source_msgs),
        target_count=len(target_msgs),
        missing=missing,
    )

    if save_csv and missing:
        csv_path = os.path.join(csv_dir, f"missing_translations_in_{locale}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Code", "Message", "Module"])
            for t in missing:
                writer.writerow([t.code, t.message, t.module])
        result.csv_path = csv_path
        logging.info(f"CSV saved: {csv_path}")

    return result


def get_auth_token(env: str) -> Optional[str]:
    creds = _env_creds(env)
    if not creds["url"] or not creds["username"] or not creds["password"]:
        logging.error(f"Missing credentials for env: {env}")
        return None
    url = f"https://{creds['url']}/user/oauth/token"
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/x-www-form-urlencoded",
        "authorization": f"Basic {os.getenv('OAUTH_BASIC_AUTH', 'ZWdvdi11c2VyLWNsaWVudDo=')}",
    }
    data = {
        "userType": "EMPLOYEE",
        "tenantId": "pb",
        "scope": "read",
        "grant_type": "password",
        "username": creds["username"],
        "password": creds["password"],
    }
    try:
        resp = requests.post(url, headers=headers, data=data, verify=False, timeout=30)
        resp.raise_for_status()
        token = resp.json()["access_token"]
        logging.info(f"Auth token fetched for {env}")
        return token
    except Exception as e:
        logging.error(f"get_auth_token failed for {env}: {e}")
        return None


def update_env_from_csv(
    target: str,
    csv_path: str = "missing_translations_in_en_IN.csv",
    locale: str = "en_IN",
    tenant_id: str = "pb",
) -> UpdateResult:
    token = get_auth_token(target)
    if not token:
        return UpdateResult(
            target_env=target,
            total_processed=0,
            total_skipped=0,
            total_upserted=0,
            error=f"Authentication failed for {target}",
        )

    creds = _env_creds(target)
    upsert_url = f"https://{creds['url']}{LOCALIZATION_UPSERT_PATH}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    processed = skipped = upserted = 0
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for row in reader:
                if len(row) < 3:
                    continue
                code, message, module = row[0], row[1], row[2]
                processed += 1
                if message in ("-", "NA"):
                    skipped += 1
                    continue
                payload = {
                    "RequestInfo": {"authToken": token},
                    "tenantId": tenant_id,
                    "messages": [
                        {
                            "code": code,
                            "message": message,
                            "module": module,
                            "locale": locale,
                        }
                    ],
                }
                resp = requests.post(
                    upsert_url, headers=headers, json=payload, verify=False, timeout=30
                )
                if resp.status_code != 200:
                    return UpdateResult(
                        target_env=target,
                        total_processed=processed,
                        total_skipped=skipped,
                        total_upserted=upserted,
                        failed_code=code,
                        error=f"HTTP {resp.status_code} on code '{code}'",
                    )
                upserted += 1
                logging.info(f"Upserted: {code}")

    except FileNotFoundError:
        return UpdateResult(
            target_env=target,
            total_processed=0,
            total_skipped=0,
            total_upserted=0,
            error=f"CSV file not found: {csv_path}. Run a comparison first.",
        )
    except Exception as e:
        return UpdateResult(
            target_env=target,
            total_processed=processed,
            total_skipped=skipped,
            total_upserted=upserted,
            error=str(e),
        )

    return UpdateResult(
        target_env=target,
        total_processed=processed,
        total_skipped=skipped,
        total_upserted=upserted,
    )
