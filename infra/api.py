from flask import Blueprint, request, jsonify, current_app
import boto3
from botocore.exceptions import ClientError
from utils.decorator import log_api_call, track_metrics, send_http_metrics
import logging

logger = logging.getLogger(__name__)
api_blueprint = Blueprint('api', __name__)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')


def get_table():
    """Get DynamoDB table instance"""
    table_name = current_app.config.get('DYNAMODB_TABLE', 'tv_show_tracker')
    return dynamodb.Table(table_name)


@api_blueprint.route('/show_episode', methods=['GET'])
@log_api_call
@track_metrics
@send_http_metrics
def show_episode():
    """Get current season and episode for a user's TV show"""
    username = request.args.get('username')
    tv_show = request.args.get('tv_show')

    if not username or not tv_show:
        logger.warning(f"Missing parameters: username={username}, tv_show={tv_show}")
        return jsonify({'error': 'Username and tv_show are required'}), 400

    try:
        table = get_table()
        response = table.get_item(
            Key={
                'username': username,
                'tv_show': tv_show
            }
        )

        if 'Item' in response:
            item = response['Item']
            logger.info(f"Retrieved episode data for {username} - {tv_show}")
            return jsonify({
                'username': item['username'],
                'tv_show': item['tv_show'],
                'season': item['season'],
                'episode': item['episode'],
                'last_updated': item.get('last_updated', '')
            })
        else:
            logger.info(f"No data found for {username} - {tv_show}")
            return jsonify({'message': 'No data found for this user and TV show'}), 404

    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in show_episode: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_blueprint.route('/show_user', methods=['GET'])
@log_api_call
@track_metrics
@send_http_metrics
def show_user():
    """Get all TV shows a user is watching"""
    username = request.args.get('username')

    if not username:
        logger.warning("Missing username parameter")
        return jsonify({'error': 'Username is required'}), 400

    try:
        table = get_table()
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('username').eq(username)
        )

        shows = []
        for item in response['Items']:
            shows.append({
                'tv_show': item['tv_show'],
                'season': item['season'],
                'episode': item['episode'],
                'last_updated': item.get('last_updated', '')
            })

        logger.info(f"Retrieved {len(shows)} shows for user {username}")
        return jsonify({
            'username': username,
            'shows': shows,
            'total_shows': len(shows)
        })

    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in show_user: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_blueprint.route('/update_episode', methods=['POST'])
@log_api_call
@track_metrics
@send_http_metrics
def update_episode():
    """Add or update episode information for a user's TV show"""
    data = request.get_json()

    if not data:
        logger.warning("No JSON data provided")
        return jsonify({'error': 'JSON data is required'}), 400

    username = data.get('username')
    tv_show = data.get('tv_show')
    season = data.get('season')
    episode = data.get('episode')

    if not all([username, tv_show, season is not None, episode is not None]):
        logger.warning(
            f"Missing parameters: username={username}, tv_show={tv_show}, season={season}, episode={episode}")
        return jsonify({'error': 'Username, tv_show, season, and episode are required'}), 400

    try:
        # Validate season and episode are integers
        season = int(season)
        episode = int(episode)

        if season < 1 or episode < 1:
            return jsonify({'error': 'Season and episode must be positive integers'}), 400

    except (ValueError, TypeError):
        logger.warning(f"Invalid season/episode format: season={season}, episode={episode}")
        return jsonify({'error': 'Season and episode must be valid integers'}), 400

    try:
        from datetime import datetime

        table = get_table()
        response = table.put_item(
            Item={
                'username': username,
                'tv_show': tv_show,
                'season': season,
                'episode': episode,
                'last_updated': datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Updated episode data for {username} - {tv_show} S{season}E{episode}")
        return jsonify({
            'message': 'Episode updated successfully',
            'username': username,
            'tv_show': tv_show,
            'season': season,
            'episode': episode
        }), 201

    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in update_episode: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_blueprint.route('/show_all', methods=['GET'])
@log_api_call
@track_metrics
@send_http_metrics
def show_all():
    """Get all entries in the table"""
    try:
        table = get_table()
        response = table.scan()

        entries = []
        for item in response['Items']:
            entries.append({
                'username': item['username'],
                'tv_show': item['tv_show'],
                'season': item['season'],
                'episode': item['episode'],
                'last_updated': item.get('last_updated', '')
            })

        # Handle pagination if there are more items
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            for item in response['Items']:
                entries.append({
                    'username': item['username'],
                    'tv_show': item['tv_show'],
                    'season': item['season'],
                    'episode': item['episode'],
                    'last_updated': item.get('last_updated', '')
                })

        logger.info(f"Retrieved all {len(entries)} entries from table")
        return jsonify({
            'entries': entries,
            'total_entries': len(entries)
        })

    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in show_all: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_blueprint.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@api_blueprint.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500