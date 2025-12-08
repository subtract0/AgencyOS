import os
from googleapiclient.discovery import build
from auth.oauth import OAuth

class CalendarTool:
    def __init__(self, oauth):
        self.oauth = oauth
        self.service = None

    def schedule_event(self, event_data):
        if not self.service:
            self.service = build('calendar', 'v3', credentials=self.oauth.creds)
        event = self.service.events().insert(calendarId='primary', body=event_data).execute()
        return event.get('id')

    def list_events(self, page_token=None):
        if not self.service:
            self.service = build('calendar', 'v3', credentials=self.oauth.creds)
        events_result = self.service.events().list(calendarId='primary', pageToken=page_token).execute()
        return events_result.get('items', [])
