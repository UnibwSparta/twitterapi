#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""compliance.py: Implementation of Twitter batch compliance.

"These batch compliance endpoints allow you to upload large datasets of Tweet or user IDs to retrieve their compliance status in order to determine what data
requires action in order to bring your datasets into compliance. Please note, use of the batch compliance endpoints is restricted to aforementioned use cases,
and any other purpose is prohibited and may result in enforcement action."
(Source: https://developer.twitter.com/en/docs/twitter-api/compliance/batch-compliance/introduction´)

Working with the batch compliance endpoints generally involves 5 steps:

#. Preparing the list of Tweet IDs or user IDs
#. Creating a compliance job
#. Uploading the list of Tweet IDs or user IDs
#. Checking the status of the compliance job
#. Downloading the results

More detailed information can be found at: https://developer.twitter.com/en/docs/twitter-api/compliance/batch-compliance/introduction

Examples:
    Creating a compliance job::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.compliance.compliance import create_compliance_job
        from sparta.twitterapi.models.twitter_v2_spec import ComplianceJobType

        compliancejobresponse = await create_compliance_job(ComplianceJobType.tweets, 'testjob')
        if not compliancejobresponse.data:
            raise Exception()
        else:
            compliancejob = compliancejobresponse.data
        jobid = compliancejob.id
        uploadurl = compliancejob.upload_url

    Uploading the list of Tweet IDs or user IDs::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.compliance.compliance import upload_ids

        await upload_ids(uploadurl, "filename.txt")

    Checking the status of the compliance job::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.compliance.compliance import list_job
        from sparta.twitterapi.models.twitter_v2_spec import ComplianceJobStatus

        async def check_job(jobid: str) -> bool:
            compliancejobresponse = await list_job(jobid)
            if not compliancejobresponse.data:
                raise Exception()
            else:
                compliancejob = compliancejobresponse.data

            if compliancejob.status == ComplianceJobStatus.complete:
                return True
            else:
                return False

        await check_job(jobid)

    Downloading the results::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.compliance.compliance import download_results, list_job

        compliancejobresponse = await list_job(jobid)
        if not compliancejobresponse.data:
            raise Exception()
        else:
            compliancejob = compliancejobresponse.data
        downloadurl = compliancejob.download_url

        await download_results(downloadurl, 'results.txt')
"""

import json
import logging
import os
from typing import Any, Dict

import aiohttp
from pydantic import AnyUrl

from sparta.twitterapi.models.twitter_v2_spec import (
    ComplianceJobStatus,
    ComplianceJobType,
    CreateComplianceJobResponse,
    Get2ComplianceJobsIdResponse,
    Get2ComplianceJobsResponse,
)

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}

COMPLIANCE_URL = "https://api.twitter.com/2/compliance/jobs"


async def create_compliance_job(type: ComplianceJobType, name: str, resumable: bool = False) -> CreateComplianceJobResponse:
    """Creates a compliance job.

    Args:
        type (str): Type of Compliance Job to list. Possible values = tweets, users
        name (str): User-provided name for a compliance job.
        resumable (bool): If true, this endpoint will return a pre-signed URL with resumable uploads enabled.

    Raises:
        Exception: Compliance Job can not be created due to an http error.

    Returns:
        CreateComplianceJobResponse: Returns an Twitter CreateComplianceJobResponse object.
    """
    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=None)) as session:
        # Set the Job request parameters.
        dataDict: Dict[str, Any] = {"type": type.name, "name": name, "resumable": resumable}

        async with session.post(COMPLIANCE_URL, data=json.dumps(dataDict)) as response:
            if not response.ok:
                raise Exception(f"Error creating Compliance Job: (HTTP {response.status}): {await response.text()}")

            return CreateComplianceJobResponse.model_validate_json(await response.text())


async def list_jobs(type: ComplianceJobType, status: ComplianceJobStatus = None) -> Get2ComplianceJobsResponse:
    """Returns recent Compliance Jobs for a given job type and optional job status.

    Args:
        type (str): Type of Compliance Job to list. Possible values = tweets, users
        status (str, optional): Status of Compliance Job to list. Possible values = created, in_progress, failed, complete. Defaults to None.

    Raises:
        Exception: Compliance Jobs can not be fetched due to an http error.

    Returns:
        Get2ComplianceJobsResponse: Returns an Twitter Get2ComplianceJobsResponse object.
    """

    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=None)) as session:
        params: Dict[str, str] = {
            "type": type.name,
        }
        if status:
            params["status"] = status.name

        async with session.get(f"{COMPLIANCE_URL}", params=params) as response:
            if not response.ok:
                raise Exception(f"Cannot get Compliance Jobs (HTTP {response.status}): {await response.text()}")
            return Get2ComplianceJobsResponse.model_validate_json(await response.text())


async def list_job(id: str) -> Get2ComplianceJobsIdResponse:
    """Returns a single Compliance Job by ID.

    Args:
        id (str): The ID of the Compliance Job to retrieve.

    Raises:
        Exception: Compliance Job can not be fetched due to an http error.

    Returns:
        Get2ComplianceJobsIdResponse: Returns an Twitter Get2ComplianceJobsIdResponse object.
    """
    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=None)) as session:
        async with session.get(f"{COMPLIANCE_URL}/{id}") as response:
            if not response.ok:
                raise Exception(f"Cannot get Compliance Job (HTTP {response.status}): {await response.text()}")
            return Get2ComplianceJobsIdResponse.model_validate_json(await response.text())


async def upload_ids(upload_url: AnyUrl, ids_file_path: str) -> str:
    """Uploads IDs for a compliance job.

    Args:
        upload_url (AnyUrl): Upload URL for a Compliance Job
        ids_file_path (str): File path where the results IDs are in. Plain text file newline separated.

    Raises:
        Exception: IDs cannot uploaded due to an http error.

    Returns:
        str: Response text
    """
    # Not passing in auth details, since the Upload URL is already signed...
    headers = {"content-type": "text/plain"}

    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=None)) as session:
        async with session.put(f"{upload_url}", data=open(ids_file_path, "rb")) as response:
            if not response.ok:
                raise Exception(f"Cannot upload IDs (HTTP {response.status}): {await response.text()}")
            return await response.text()


async def download_results(download_url: AnyUrl, results_file_path: str) -> int:
    """Downloads the results of a compliance job and saves them to a file.

    Args:
        download_url (AnyUrl): Download URL for a Jompliance Job
        results_file_path (str): File path where the results will be saved.

    Raises:
        Exception: Results can not be fetched due to an http error.
        Exception: Results can not be writen into the file.

    Returns:
        int: Respone status.
    """
    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=None)) as session:
        async with session.get(f"{download_url}") as response:
            if not response.ok:
                raise Exception(f"Cannot download results (HTTP {response.status}): {await response.text()}")

            try:
                with open(results_file_path, "w") as f:
                    f.write(await response.text())
            except Exception:
                raise Exception(f"Error writing results to {results_file_path}")
            return response.status
