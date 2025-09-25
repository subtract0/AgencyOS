"""
Tests for Registry REST API - ensuring robust web interface.

Every test verifies essential API functionality.
"""

import json
import pytest
import tempfile
import os
from unittest.mock import patch

from meta_learning.registry_api import create_app
from meta_learning.agent_registry import AgentRegistry


@pytest.fixture
def temp_registry():
    """Create temporary registry for testing."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    registry = AgentRegistry(storage_path=temp_file.name)
    yield registry
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def client(temp_registry):
    """Create test client."""
    app = create_app(temp_registry)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestRegistryAPIBasic:
    """Test basic API functionality."""

    def test_health_check(self, client):
        """Test health endpoint."""
        response = client.get('/health')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'agents_count' in data

    def test_create_agent_valid(self, client):
        """Test creating valid agent."""
        response = client.post('/agents',
                             json={'name': 'TestAgent', 'version': '1.0.0'})
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['name'] == 'TestAgent'
        assert data['version'] == '1.0.0'
        assert 'agent_id' in data

    def test_create_agent_minimal(self, client):
        """Test creating agent with minimal data."""
        response = client.post('/agents', json={'name': 'MinimalAgent'})
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['name'] == 'MinimalAgent'
        assert data['version'] == '1.0.0'  # Default version

    def test_create_agent_missing_name(self, client):
        """Test creating agent without name."""
        response = client.post('/agents', json={})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data

    def test_create_agent_no_json(self, client):
        """Test creating agent without JSON data."""
        response = client.post('/agents')
        assert response.status_code == 400


class TestRegistryAPIInstances:
    """Test instance management."""

    def test_create_instance_valid(self, client):
        """Test creating valid instance."""
        # First create agent
        agent_response = client.post('/agents', json={'name': 'TestAgent'})
        agent_id = json.loads(agent_response.data)['agent_id']

        # Create instance
        config = {'param1': 'value1', 'param2': 42}
        response = client.post(f'/agents/{agent_id}/instances', json={'config': config})
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['agent_id'] == agent_id
        assert data['config'] == config
        assert 'instance_id' in data

    def test_create_instance_no_config(self, client):
        """Test creating instance without config."""
        # First create agent
        agent_response = client.post('/agents', json={'name': 'TestAgent'})
        agent_id = json.loads(agent_response.data)['agent_id']

        # Create instance without config
        response = client.post(f'/agents/{agent_id}/instances')
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['config'] == {}

    def test_create_instance_invalid_agent(self, client):
        """Test creating instance for non-existent agent."""
        response = client.post('/agents/invalid-id/instances', json={})
        assert response.status_code == 404

        data = json.loads(response.data)
        assert 'error' in data


class TestRegistryAPIAIQ:
    """Test AIQ recording and retrieval."""

    def test_record_aiq_valid(self, client):
        """Test recording valid AIQ."""
        # Setup: create agent and instance
        agent_response = client.post('/agents', json={'name': 'TestAgent'})
        agent_id = json.loads(agent_response.data)['agent_id']

        instance_response = client.post(f'/agents/{agent_id}/instances', json={})
        instance_id = json.loads(instance_response.data)['instance_id']

        # Record AIQ
        metrics = {'accuracy': 0.95, 'speed': 1.2}
        response = client.post(f'/instances/{instance_id}/aiq',
                              json={'aiq_score': 87.5, 'metrics': metrics})
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['instance_id'] == instance_id
        assert data['aiq_score'] == 87.5
        assert 'event_id' in data

    def test_record_aiq_no_metrics(self, client):
        """Test recording AIQ without metrics."""
        # Setup
        agent_response = client.post('/agents', json={'name': 'TestAgent'})
        agent_id = json.loads(agent_response.data)['agent_id']

        instance_response = client.post(f'/agents/{agent_id}/instances', json={})
        instance_id = json.loads(instance_response.data)['instance_id']

        # Record AIQ without metrics
        response = client.post(f'/instances/{instance_id}/aiq',
                              json={'aiq_score': 80.0})
        assert response.status_code == 201

    def test_record_aiq_missing_score(self, client):
        """Test recording AIQ without score."""
        response = client.post('/instances/some-id/aiq', json={})
        assert response.status_code == 400

    def test_record_aiq_invalid_instance(self, client):
        """Test recording AIQ for non-existent instance."""
        response = client.post('/instances/invalid-id/aiq',
                              json={'aiq_score': 75.0})
        assert response.status_code == 404

    def test_get_aiq_history(self, client):
        """Test getting AIQ history."""
        # Setup: create agent, instance, and record AIQ
        agent_response = client.post('/agents', json={'name': 'TestAgent'})
        agent_id = json.loads(agent_response.data)['agent_id']

        instance_response = client.post(f'/agents/{agent_id}/instances', json={})
        instance_id = json.loads(instance_response.data)['instance_id']

        # Record multiple AIQ events
        client.post(f'/instances/{instance_id}/aiq', json={'aiq_score': 85.0})
        client.post(f'/instances/{instance_id}/aiq', json={'aiq_score': 87.5})

        # Get history
        response = client.get(f'/agents/{agent_id}/aiq-history')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['agent_id'] == agent_id
        assert len(data['events']) == 2
        # Should be sorted newest first
        assert data['events'][0]['aiq_score'] == 87.5
        assert data['events'][1]['aiq_score'] == 85.0

    def test_get_aiq_history_with_limit(self, client):
        """Test getting AIQ history with limit."""
        # Setup
        agent_response = client.post('/agents', json={'name': 'TestAgent'})
        agent_id = json.loads(agent_response.data)['agent_id']

        instance_response = client.post(f'/agents/{agent_id}/instances', json={})
        instance_id = json.loads(instance_response.data)['instance_id']

        # Record multiple events
        for score in [80.0, 82.0, 85.0]:
            client.post(f'/instances/{instance_id}/aiq', json={'aiq_score': score})

        # Get history with limit
        response = client.get(f'/agents/{agent_id}/aiq-history?limit=2')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert len(data['events']) == 2

    def test_get_top_performers(self, client):
        """Test getting top performers."""
        # Setup multiple agents with different scores
        agents = []
        for i, name in enumerate(['Agent1', 'Agent2', 'Agent3']):
            agent_resp = client.post('/agents', json={'name': name})
            agent_id = json.loads(agent_resp.data)['agent_id']
            agents.append(agent_id)

            instance_resp = client.post(f'/agents/{agent_id}/instances', json={})
            instance_id = json.loads(instance_resp.data)['instance_id']

            # Record different scores
            score = 80.0 + (i * 5)  # 80, 85, 90
            client.post(f'/instances/{instance_id}/aiq', json={'aiq_score': score})

        # Get top performers
        response = client.get('/agents/top-performers')
        assert response.status_code == 200

        data = json.loads(response.data)
        performers = data['top_performers']

        # Should be sorted by score descending
        assert len(performers) == 3
        assert performers[0]['name'] == 'Agent3'
        assert performers[0]['aiq_score'] == 90.0
        assert performers[2]['name'] == 'Agent1'
        assert performers[2]['aiq_score'] == 80.0

    def test_get_top_performers_with_limit(self, client):
        """Test top performers with limit."""
        # Setup 3 agents
        for i, name in enumerate(['Agent1', 'Agent2', 'Agent3']):
            agent_resp = client.post('/agents', json={'name': name})
            agent_id = json.loads(agent_resp.data)['agent_id']

            instance_resp = client.post(f'/agents/{agent_id}/instances', json={})
            instance_id = json.loads(instance_resp.data)['instance_id']

            client.post(f'/instances/{instance_id}/aiq', json={'aiq_score': 80.0 + i})

        # Get with limit
        response = client.get('/agents/top-performers?limit=2')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert len(data['top_performers']) == 2


class TestRegistryAPIErrorHandling:
    """Test error handling and edge cases."""

    def test_malformed_json(self, client):
        """Test handling of malformed JSON."""
        response = client.post('/agents',
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400

    @patch('meta_learning.registry_api.AgentRegistry')
    def test_server_error_handling(self, mock_registry_class, client):
        """Test server error handling."""
        # Mock registry to raise exception
        mock_registry = mock_registry_class.return_value
        mock_registry.register_agent.side_effect = Exception("Database error")

        app = create_app(mock_registry)
        app.config['TESTING'] = True

        with app.test_client() as test_client:
            response = test_client.post('/agents', json={'name': 'TestAgent'})
            assert response.status_code == 500

    def test_invalid_float_aiq_score(self, client):
        """Test invalid AIQ score handling."""
        # Setup
        agent_response = client.post('/agents', json={'name': 'TestAgent'})
        agent_id = json.loads(agent_response.data)['agent_id']

        instance_response = client.post(f'/agents/{agent_id}/instances', json={})
        instance_id = json.loads(instance_response.data)['instance_id']

        # Try to record non-numeric score
        response = client.post(f'/instances/{instance_id}/aiq',
                              json={'aiq_score': 'not a number'})
        assert response.status_code == 400  # Now properly handled as bad request


if __name__ == "__main__":
    # Skip nested pytest execution to prevent recursion
    import os
    if os.environ.get("AGENCY_NESTED_TEST") != "1":
        pytest.main([__file__, "-v"])