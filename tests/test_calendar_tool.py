import unittest
from unittest.mock import patch, MagicMock
from tools.life.calendar_tool import CalendarTool
from auth.oauth import OAuth

class TestCalendarTool(unittest.TestCase):
    def setUp(self):
        self.oauth = OAuth('client_secret.json')
        self.calendar_tool = CalendarTool(self.oauth)

    @patch('googleapiclient.discovery.build')
    def test_schedule_event(self, mock_build):
        event_data = {'summary': 'Test Event'}
        mock_service = MagicMock()
        mock_service.events.return_value.insert.return_value.execute.return_value = {'id': 'test-event-id'}
        mock_build.return_value = mock_service
        event_id = self.calendar_tool.schedule_event(event_data)
        self.assertEqual(event_id, 'test-event-id')

    @patch('googleapiclient.discovery.build')
    def test_list_events(self, mock_build):
        events_data = [{'summary': 'Test Event 1'}, {'summary': 'Test Event 2'}]
        mock_service = MagicMock()
        mock_service.events.return_value.list.return_value.execute.return_value = {'items': events_data}
        mock_build.return_value = mock_service
        events = self.calendar_tool.list_events()
        self.assertEqual(len(events), 2)
