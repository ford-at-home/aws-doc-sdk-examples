# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Purpose

Shows ya how to use the AWS SDK for Python (Boto3) with AWS Audit Manager to create an
assessment report that consists of only one day of evidence.
"""

import dateutil.parser
import logging
import time
import urllib.request
import uuid
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AuditReport:
    def __init__(self, auditmanager_client):
        self.auditmanager_client = auditmanager_client

    @staticmethod
    def validate_uuid(value):
        """Validates whether the provided value is a valid UUID."""
        try:
            return uuid.UUID(value)
        except ValueError:
            logger.error("Provided value is not a valid UUID: %s", value)
            raise

    @staticmethod
    def parse_date(value):
        """Parses the date from a string, returning a date object."""
        try:
            return dateutil.parser.parse(value).date()
        except ValueError:
            logger.error("Invalid date format: %s", value)
            raise

    def get_assessment_input(self):
        """Collects user input for the assessment ID and evidence date."""
        print("-" * 40)
        assessment_id = input("Provide assessment ID [UUID]: ").strip().lower()
        evidence_date_str = input("Provide evidence date [YYYY-MM-DD]: ").strip()
        assessment_uuid = self.validate_uuid(assessment_id)
        evidence_date = self.parse_date(evidence_date_str)
        
        # Verify the assessment exists
        try:
            self.auditmanager_client.get_assessment(assessmentId=str(assessment_uuid))
        except ClientError as error:
            logger.exception("Failed to get assessment %s.", assessment_uuid)
            raise error

        return assessment_uuid, evidence_date

    def clear_staging(self, assessment_uuid, evidence_date):
        """Clears existing evidence from staging area."""
        interested_folders = self.find_evidence_folders(assessment_uuid, evidence_date)
        for folder_id in interested_folders:
            self.remove_folder_from_report(assessment_uuid, folder_id)

    def find_evidence_folders(self, assessment_uuid, evidence_date):
        """Finds evidence folders by date."""
        folders_to_include = []
        paginator = self.auditmanager_client.get_paginator('get_evidence_folders_by_assessment')
        for page in paginator.paginate(assessmentId=str(assessment_uuid)):
            for folder in page['evidenceFolders']:
                if folder['name'] == str(evidence_date):
                    folders_to_include.append(folder['id'])
        return folders_to_include

    def remove_folder_from_report(self, assessment_uuid, folder_id):
        """Removes a folder from the report."""
        self.auditmanager_client.disassociate_assessment_report_evidence_folder(
            assessmentId=str(assessment_uuid), evidenceFolderId=folder_id)

    def add_folder_to_staging(self, assessment_uuid, folder_id_list):
        """Adds folders to the staging area for the report."""
        for folder_id in folder_id_list:
            self.auditmanager_client.associate_assessment_report_evidence_folder(
                assessmentId=str(assessment_uuid), evidenceFolderId=folder_id)

    def generate_report(self, assessment_uuid):
        """Generates the assessment report."""
        report_id = self.create_report(assessment_uuid)
        if self.wait_for_report_generation(report_id):
            self.download_report(assessment_uuid, report_id)
        else:
            logger.info("Report generation did not complete in the allocated time.")

    def create_report(self, assessment_uuid):
        """Creates an assessment report and returns its ID."""
        report = self.auditmanager_client.create_assessment_report(
            name="ReportViaScript",
            description="Report generated via script.",
            assessmentId=str(assessment_uuid))
        return report['assessmentReport']['id']

    def wait_for_report_generation(self, report_id, timeout=900, interval=5):
        """Waits for a report to be generated, returning True if successful."""
        elapsed_time = 0
        while elapsed_time < timeout:
            report_status = self.auditmanager_client.get_assessment_report_status(
                assessmentReportId=report_id)['status']
            if report_status == 'COMPLETE':
                return True
            time.sleep(interval)
            elapsed_time += interval
        return False

    def download_report(self, assessment_uuid, report_id):
        """Downloads the generated report."""
        report_url = self.auditmanager_client.get_assessment_report_url(
            assessmentReportId=report_id, assessmentId=str(assessment_uuid))['url']
        file_name = f"{uuid.uuid4()}.pdf"
        urllib.request.urlretrieve(report_url, file_name)
        logger.info("Report saved as %s.", file_name)

def run_demo():
    """Entry point for the demo script."""
    print("-" * 88)
    print("AWS Audit Manager Assessment Report Generation")
    print("-" * 88)

    audit_manager_client = boto3.client("auditmanager")
    report_generator = AuditReport(audit_manager_client)

    try:
        assessment_uuid, evidence_date = report_generator.get_assessment_input()
        folder_id_list = report_generator.clear_staging(assessment_uuid, evidence_date)
        report_generator.add_folder_to_staging(assessment_uuid, folder_id_list)
        report_generator.generate_report(assessment_uuid)
    except Exception as e:
        logger.error("An error occurred: %s", e)

if __name__ == "__main__":
    run_demo()
