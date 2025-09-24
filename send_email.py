"""
PURPOSE:
    This script is used to send an email using Logic App

LOGIC:
    It sends an email using a Logic App HTTP trigger in Azure.
    The function constructs a JSON payload with the email data
    and sends a POST request to the Logic App URL.

INPUTS:
    It takes four parameters:
        to (recipient's email), subject, mailbody, and content_bytes (attachment).

OUTPUTS:
    If the request is successful, it logs a success message;
    otherwise, it logs an error message and raises an exception.
"""

import json
import logging

import requests

from config import Config


logger = logging.getLogger(__name__)


def send_mail(to, cc, subject, mailbody):
    """
    This method sends an email to the recipient using Logic App HTTP trigger.
    Logic App HTTP trigger is not safeguarded now with any tokens or keys.
    Also the Logic App logged in using 'pandiarajans@test.com',
    and so the from address is constant now.
    """

    url = Config.LOGIC_APP_EMAIL_URL
    from_email = Config.LOGIC_APP_FROM_EMAIL
    email_optout = Config.EMAIL_OPTOUT

    if email_optout:
        logger.warning(
            f"Email sending is disabled via EMAIL_OPTOUT env var. "
            f"Skipping sending email to: {to} \n "
            f"with subject: {subject} \n "
            f"and mailbody: {mailbody} \n Cancelled"
        )
        return

    if not url:
        logger.error("LOGIC_APP_EMAIL_URL is not configured. Cannot send email.")
        raise ValueError("LOGIC_APP_EMAIL_URL is required for email functionality")

    email_header = {"Content-Type": "application/json"}

    email_data = {"to": f"{to}", "cc": f"{cc}", "from": from_email, "subject": f"{subject}", "mailbody": f"{mailbody}"}

    try:
        response = requests.post(url, headers=email_header, data=json.dumps(email_data), timeout=30)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        raise
    except Exception as err:
        logger.error(f"Error sending email: {err}")
        raise

    logger.info(f"Email sent successfully to {to}")
