#!/usr/bin/env python3

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from scraper import Params

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

SPREADSHEET_ID = os.environ["GSHEETS_SPREADSHEET_ID"]
RANGE_NAME = 'Form Responses 1'

def main():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        # first row is header
        values = values[0:1] + sorted(values[1:], key=lambda v: v[0]) # sort by timestamp
        subscriptions_list = []
        print(values[0])
        for row in values[1:]:
            assert len(row) == Params.SPREADSHEET_NUM_COLS, row
            row[Params.SPREADSHEET_PHONE_INDEX] = "+1"+row[Params.SPREADSHEET_PHONE_INDEX]
            assert(row[Params.SPREADSHEET_CONSENT_INDEX] == "Yes")
            assert(row[Params.SPREADSHEET_SUB_INDEX] in ["Subscribe", "Unsubscribe"])
            if (row[Params.SPREADSHEET_SUB_INDEX] == "Subscribe"):
                subscriptions_list.append(row)
                newsize = len(subscriptions_list)
                print('SUB:', ','.join(row), "newsize:", newsize)
            else:
                origsize = len(subscriptions_list)
                subscriptions_list = list(filter(lambda s: s[Params.SPREADSHEET_PHONE_INDEX] != row[Params.SPREADSHEET_PHONE_INDEX], subscriptions_list))
                newsize = len(subscriptions_list)
                print('UNSUB:', ','.join(row), " oldsize:", origsize, "newsize:", newsize)
        print(f'Found {len(subscriptions_list)} subscriptions. Exporting...')
        with open('sheets.csv', 'w+') as f:
            f.write('\n'.join(map(lambda x: ','.join(x[3:]), subscriptions_list))+'\n')

if __name__ == '__main__':
    main()
