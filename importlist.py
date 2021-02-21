#!/usr/bin/env python3

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

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
        values = values[0:1] + sorted(values[1:], key=lambda v: v[0]) # sort by timestamp
        # TODO: add unsubscription logic
        for i,row in enumerate(values):
            assert len(row) == 7, row
            if i > 0:
                row[6] = "+1"+row[6]
            print(','.join(row))
        print(f'Found {len(values)-1} rows. Exporting...')
        with open('sheets.csv', 'w+') as f:
            f.write('\n'.join(map(lambda x: ','.join(x[2:]), filter(lambda v: "Subscribe" in v, values[1:])))+'\n')

if __name__ == '__main__':
    main()
