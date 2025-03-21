import json
import pathlib
import string

import requests

from configuration import keyvault


def get_token(env):
    response = requests.request(method="POST",
                                url=keyvault[env]["token_url"],
                                headers={"content-type": "application/x-www-form-urlencoded"},
                                data=f"grant_type=client_credentials&client_id={keyvault[env]["client_id"]}&client_secret={keyvault[env]["client_secret"]}&scope={keyvault[env]["scope"]} {keyvault[env]["client_id"]}")

    if response.status_code == 200:
        print(f"********* Token Generated Successfully ************")
        response_dict = json.loads(response.text)
        return "Bearer " + response_dict["access_token"]
    else:
        print(f"Error occurred while creating token. {response.text}")
        # exit(1)


def prepare_schema(schema_file_name):
    path = pathlib.Path(schema_file_name)
    with open(path) as fp:
        json_response = json.load(fp)
        return json_response


def create_schema(env, dag, target_kind) -> (bool, string):
    url = f"{keyvault[env]["adme_dns_host"]}/api/schema-service/v1/schema"
    osdu_token = get_token(env)
    authority, source, entity_type, version = target_kind.split(":")[0:4]
    print(f"{authority, source, entity_type, version, target_kind}")
    major, minor, patch = version.split(".")
    print(f"{major, minor, patch}")
    schema_mapper = {"csv_parser_wf_status_gsm": ["csv_parser_schema.json"],
                     "doc_ingestor_azure_ocr_wf": ["document_schema.json"],
                     "wellbore_ingestion_wf_gsm": ["well_log_schema.json",
                                                   "well_trajectory_schema.json"],
                     "shapefile_ingestor_wf_status_gsm": ["shapefile_schema.json"],
                     }
    payload = json.dumps({
        "schema": prepare_schema(schema_mapper[dag][0]),
        "schemaInfo": {
            "createdBy": "pgorade@slb.com",
            "schemaIdentity": {
                "authority": f"{authority}",
                "entityType": f"{entity_type}",
                "id": f"{target_kind}",
                "schemaVersionMajor": f"{major}",
                "schemaVersionMinor": f"{minor}",
                "schemaVersionPatch": f"{patch}",
                "source": f"{source}"
            },
            "scope": "INTERNAL",
            "status": "DEVELOPMENT"

        }
    })
    headers = {
        'data-partition-id': f'{keyvault[env]["data_partition_id"]}',
        'Authorization': f'{osdu_token}',
        'Content-Type': 'application/json'
    }
    authority, source, entity_type = target_kind.split(":")[0:3]
    print(f"{authority=},{source=},{entity_type=}")
    print("got token = ", osdu_token)

    print(f"{payload=}")
    response = requests.request("POST", url, headers=headers, data=payload)
    print(f"{response.text}")
    response_body = json.loads(response.content)
    if response.status_code == 201:
        # schema_id = response_body.get("schemaInfos")[0].get("schemaIdentity").get("id")
        return response_body.get("schemaIdentity").get("id")
    else:
        print("Error occurred while creating schema ", response.status_code, response.text)


if __name__ == "__main__":
    args = ("evd-ltops", "csv_parser_wf_status_gsm", "osdu:wks:wellbore:1.5.1")
    create_schema(*args)
