import unittest
from unittest.mock import Mock, patch
from tools.life.calendar_tool import CalendarTool
from googleapiclient.discovery import build

class TestCalendarTool(unittest.TestCase):
    def setUp(self):
        self.mock_service = Mock()
        self.mock_service.events.return_value.list.return_value.execute.return_value.get.return_value = []
        self.calendar_tool = CalendarTool(self.mock_service)

    @patch('google-auth.oauth2.credentials.Credentials.refresh')
    def test_oauth_flow(self, mock_refresh):
        credentials = Mock()
        credentials.refresh.return_value = 'new_token'
        self.calendar_tool.oauth_flow(credentials)
        self.assertEqual(mock_refresh.call_count, 1)

    @patch('googleapiclient.discovery.build')
    def test_schedule_event(self, mock_build):
        event_data = {'summary': 'Test Event', 'start': {'date': '2024-03-16'}, 'end': {'date': '2024-03-17'}}
        self.calendar_tool.schedule_event(event_data)
        mock_build.assert_called_once_with('calendar', 'v3')

    @patch('googleapiclient.discovery.build')
    def test_list_events(self, mock_build):
        events = [{'summary': 'Event 1'}, {'summary': 'Event 2'}]
        self.mock_service.events.return_value.list.return_value.execute.return_value.get.return_value = events
        result = self.calendar_tool.list_events()
        self.assertEqual(result, events)

if __name__ == '__main__':
    unittest.main()
