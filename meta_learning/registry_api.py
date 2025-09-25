"""
Agent Registry REST API - Minimal viable web interface.

Focused on essential endpoints that add immediate value.
"""

from flask import Flask, request, jsonify
from datetime import datetime
from typing import Dict, Any

from .agent_registry import AgentRegistry


def create_app(registry: AgentRegistry = None) -> Flask:
    """Create Flask app with registry endpoints."""
    app = Flask(__name__)

    if registry is None:
        registry = AgentRegistry()

    @app.route('/agents', methods=['POST'])
    def create_agent():
        """Register new agent."""
        try:
            data = request.get_json(force=True, silent=True)
            if not data or 'name' not in data:
                return jsonify({'error': 'Agent name required'}), 400

            agent_id = registry.register_agent(
                name=data['name'],
                version=data.get('version', '1.0.0')
            )

            return jsonify({
                'agent_id': agent_id,
                'name': data['name'],
                'version': data.get('version', '1.0.0')
            }), 201

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/agents/<agent_id>/instances', methods=['POST'])
    def create_instance(agent_id: str):
        """Create agent instance."""
        try:
            data = request.get_json(force=True, silent=True) or {}
            config = data.get('config', {})

            instance_id = registry.create_instance(agent_id, config)

            return jsonify({
                'instance_id': instance_id,
                'agent_id': agent_id,
                'config': config
            }), 201

        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/instances/<instance_id>/aiq', methods=['POST'])
    def record_aiq(instance_id: str):
        """Record AIQ measurement."""
        try:
            data = request.get_json(force=True, silent=True)
            if not data or 'aiq_score' not in data:
                return jsonify({'error': 'aiq_score required'}), 400

            try:
                aiq_score = float(data['aiq_score'])
            except (ValueError, TypeError):
                return jsonify({'error': 'aiq_score must be a number'}), 400

            event_id = registry.record_aiq(
                instance_id=instance_id,
                aiq_score=aiq_score,
                metrics=data.get('metrics', {})
            )

            return jsonify({
                'event_id': event_id,
                'instance_id': instance_id,
                'aiq_score': aiq_score
            }), 201

        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/agents/<agent_id>/aiq-history')
    def get_aiq_history(agent_id: str):
        """Get AIQ history for agent."""
        try:
            limit = request.args.get('limit', 10, type=int)
            history = registry.get_agent_aiq_history(agent_id, limit=limit)

            return jsonify({
                'agent_id': agent_id,
                'events': [
                    {
                        'event_id': event.event_id,
                        'aiq_score': event.aiq_score,
                        'timestamp': event.timestamp.isoformat(),
                        'metrics': event.metrics
                    }
                    for event in history
                ]
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/agents/top-performers')
    def get_top_performers():
        """Get top performing agents."""
        try:
            limit = request.args.get('limit', 5, type=int)
            performers = registry.get_top_performers(limit=limit)

            return jsonify({
                'top_performers': [
                    {'name': name, 'aiq_score': score}
                    for name, score in performers
                ]
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/health')
    def health_check():
        """Simple health check."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'agents_count': len(registry.agents),
            'instances_count': len(registry.instances),
            'events_count': len(registry.aiq_events)
        })

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)