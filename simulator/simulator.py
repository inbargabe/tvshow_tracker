#!/usr/bin/env python3
"""
Simple TV Show Tracker Simulator
Runs every interval and either queries or updates data
"""

import requests
import random
import time
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5000/api"
INTERVAL_SECONDS = 10

# Sample data for simulation
USERS = ["alice", "bob", "charlie", "diana", "eve"]
TV_SHOWS = [
    "Breaking Bad", "The Office", "Stranger Things", "Game of Thrones",
    "Friends", "The Crown", "Ozark", "House of Cards", "Narcos",
    "Black Mirror", "Sherlock", "Lost", "Prison Break", "Dexter"
]


def log_message(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def query_all_data():
    """Query all entries in the database"""
    try:
        response = requests.get(f"{API_BASE_URL}/show_all", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_message(f"QUERY_ALL: Found {data.get('total_entries', 0)} entries")
            return True
        else:
            log_message(f"ERROR: Query all failed - Status: {response.status_code}")
            return False
    except Exception as e:
        log_message(f"ERROR: Query all error: {str(e)}")
        return False


def query_user_data():
    """Query a random user's data"""
    user = random.choice(USERS)
    try:
        response = requests.get(f"{API_BASE_URL}/show_user", params={"username": user}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_message(f"QUERY_USER: User '{user}' has {data.get('total_shows', 0)} shows")
            return True
        else:
            log_message(f"ERROR: Query user failed - Status: {response.status_code}")
            return False
    except Exception as e:
        log_message(f"ERROR: Query user error: {str(e)}")
        return False


def query_specific_episode():
    """Query a specific episode for a user"""
    user = random.choice(USERS)
    show = random.choice(TV_SHOWS)
    try:
        params = {"username": user, "tv_show": show}
        response = requests.get(f"{API_BASE_URL}/show_episode", params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_message(f"QUERY_EPISODE: {user} watching {show} S{data['season']}E{data['episode']}")
            return True
        elif response.status_code == 404:
            log_message(f"QUERY_EPISODE: No data found for {user} - {show}")
            return True
        else:
            log_message(f"ERROR: Query episode failed - Status: {response.status_code}")
            return False
    except Exception as e:
        log_message(f"ERROR: Query episode error: {str(e)}")
        return False


def update_episode():
    """Add or update an episode for a random user"""
    user = random.choice(USERS)
    show = random.choice(TV_SHOWS)
    season = random.randint(1, 10)
    episode = random.randint(1, 24)

    data = {
        "username": user,
        "tv_show": show,
        "season": season,
        "episode": episode
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/update_episode",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 201:
            log_message(f"UPDATE: {user} watching {show} S{season}E{episode}")
            return True
        else:
            log_message(f"ERROR: Update failed - Status: {response.status_code}")
            return False
    except Exception as e:
        log_message(f"ERROR: Update error: {str(e)}")
        return False


def run_simulation():
    """Main simulation function"""
    actions = [
        ("Query All Data", query_all_data, 0.2),
        ("Query User Data", query_user_data, 0.3),
        ("Query Episode", query_specific_episode, 0.2),
        ("Update Episode", update_episode, 0.3)
    ]

    # Choose action based on weights
    rand = random.random()
    cumulative = 0

    for action_name, action_func, weight in actions:
        cumulative += weight
        if rand <= cumulative:
            log_message(f"ACTION: {action_name}")
            success = action_func()
            if success:
                log_message(f"SUCCESS: {action_name} completed")
            else:
                log_message(f"FAILED: {action_name} failed")
            break


def main():

    log_message("Starting TV Show Tracker Simulator")
    log_message(f"API Base URL: {API_BASE_URL}")
    log_message(f"Interval: {INTERVAL_SECONDS} seconds")
    log_message("Press Ctrl+C to stop")

    try:
        while True:
            run_simulation()
            log_message(f"Waiting {INTERVAL_SECONDS} seconds...")
            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        log_message("Simulator stopped by user")
    except Exception as e:
        log_message(f"ERROR: Simulator crashed: {str(e)}")


if __name__ == "__main__":
    main()