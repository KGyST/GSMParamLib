#!C:\Program Files\Python27amd64\python.exe
# -*- coding: utf-8 -*-
"""
Author: Sam KARLI
E-mail: karliterv@gmail.com
Date: 
Description:
THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY WARRANTIES OF ANY KIND.
"""

import pip
from Config import *
from configparser import *  #FIXME not *

try:
  import googleapiclient.errors
  from googleapiclient.discovery import build
  from google_auth_oauthlib.flow import InstalledAppFlow, Flow
  from google.auth.transport.requests import Request
  from google.oauth2.credentials import Credentials

except ImportError:
  pip.main(['install', '--user', 'google-api-python-client'])
  pip.main(['install', '--user', 'google-auth-httplib2'])
  pip.main(['install', '--user', 'google-auth-oauthlib'])

  import googleapiclient.errors
  from googleapiclient.discovery import build
  from google_auth_oauthlib.flow import InstalledAppFlow
  from google.auth.transport.requests import Request
  from google.oauth2.credentials import Credentials


# ------------------- Google Spreadsheet API connectivity --------------------------------------------------------------

class NoGoogleCredentialsException(Exception):
  pass

class GoogleSpreadsheetConnector(object):
  GOOGLE_SPREADSHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

  def __init__(self, current_config: 'Config', inSpreadsheetID):
    #FIXME renaming/filling out these
    client_config = {"installed": {
      "client_id": "224241213692-7gafn34d4heprhps1rod3clt1b8j07j6.apps.googleusercontent.com",
      "project_id": "quickstart-1558854893881",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_secret": "PHWQx7k6ldF73rDkqJE2Cedl",
      "redirect_uris": {
        "urn:ietf:wg:oauth:2.0:oob",
        "http://localhost"}
    }}

    current_config.setCurrentSection("Google")

    try:
      if  "access_token" in current_config \
      and "refresh_token" in current_config \
      and "token_type" in current_config \
      and "id_token" in current_config \
      and "token_uri" in current_config \
      and "client_id" in current_config \
      and "client_secret" in current_config:
        self.googleCreds = Credentials(
          token=          current_config["access_token"],
          refresh_token=  current_config["refresh_token"],
          id_token=       current_config["id_token"],
          token_uri=      current_config["token_uri"],
          client_id=      current_config["client_id"],
          client_secret=  current_config["client_secret"],
          scopes=         GoogleSpreadsheetConnector.GOOGLE_SPREADSHEET_SCOPES
        )

        if not self.googleCreds.valid:
          if self.googleCreds.expired and self.googleCreds.refresh_token:
            self.googleCreds.refresh(Request())
          else:
            raise NoGoogleCredentialsException
      else:
        raise NoGoogleCredentialsException

    except (NoSectionError, NoOptionError, NoGoogleCredentialsException):
      flow = InstalledAppFlow.from_client_config(client_config, GoogleSpreadsheetConnector.GOOGLE_SPREADSHEET_SCOPES)
      self.googleCreds = flow.run_local_server()

    try:
      service = build('sheets', 'v4', credentials=self.googleCreds)

      sheet = service.spreadsheets()

      _execute = sheet.get(spreadsheetId=inSpreadsheetID, includeGridData=True).execute()
      sheetName = _execute['sheets'][0]['properties']['title']

      result = sheet.values().get(spreadsheetId=inSpreadsheetID,
                                        range=sheetName).execute()

      self.values = result.get('values', [])

      if not self.values:
        print('No data found.')
      # else:
      #     for row in self.values:
      #         print('%s, %s' % (row[0], row[4]))
    except googleapiclient.errors.HttpError:
      SSIDRegex = "/spreadsheets/d/([a-zA-Z0-9-_]+)"
      print(("HttpError: Spreadsheet ID (%s) seems to be invalid" % SSIDRegex))
      return
