import argparse
import requests
from prettytable import PrettyTable

# Step 1: Input Handling
def get_usernames():
    """
    Fetch a list of usernames from a file or a comma-separated list provided as input.
    """
    parser = argparse.ArgumentParser(description="Fetch LeetCode user profile data.")
    parser.add_argument(
        "-f", "--file",
        help="Path to a file containing usernames (one username per line)."
    )
    parser.add_argument(
        "-u", "--usernames",
        help="Comma-separated list of usernames."
    )
    args = parser.parse_args()

    usernames = []
    if args.file:
        try:
            with open(args.file, "r") as file:
                usernames = [line.strip() for line in file.readlines()]
        except FileNotFoundError:
            raise ValueError(f"File not found: {args.file}")
    elif args.usernames:
        usernames = [username.strip() for username in args.usernames.split(",")]
    else:
        raise ValueError("Provide either a file path or a list of usernames.")

    # Ensure the number of usernames does not exceed 100
    if len(usernames) > 100:
        raise ValueError("The number of usernames cannot exceed 100.")

    return usernames

# Step 2: Fetch User Data from LeetCode GraphQL API
def fetch_user_data(username):
    """
    Fetches LeetCode user profile data using the GraphQL API.
    :param username: LeetCode username.
    :return: A dictionary containing user data or an error message.
    """
    url = "https://leetcode.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/{username}/",
        "User-Agent": "Mozilla/5.0 (compatible; LeetCodeFetcher/1.0)"
    }

    # GraphQL query to fetch user profile data
    query = """
    query getUserProfile($username: String!) {
      matchedUser(username: $username) {
        username
        profile {
          realName
          userAvatar
          ranking
        }
        submitStats {
          acSubmissionNum {
            difficulty
            count
          }
        }
        badges {
          displayName
        }
      }
    }
    """
    payload = {
        "operationName": "getUserProfile",
        "query": query,
        "variables": {"username": username}
    }

    # Send the POST request to the GraphQL endpoint
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        return {"username": username, "error": f"API error: {response.status_code}"}

    try:
        # Parse the JSON response
        data = response.json()
        if "errors" in data:
            return {"username": username, "error": data["errors"]}

        user_data = data["data"]["matchedUser"]
        if not user_data:
            return {"username": username, "error": "User not found."}

        profile = user_data["profile"]
        submissions = user_data["submitStats"]["acSubmissionNum"]
        badges = user_data.get("badges", [])

        return {
            "username": username,
            "ranking": profile["ranking"],
            "problems_solved": sum(item["count"] for item in submissions)//2,
            "badges": [badge["displayName"] for badge in badges]
        }
    except ValueError as e:
        return {"username": username, "error": f"Invalid API response: {e}"}

# Step 3: Fetch Data for All Users
def fetch_all_users(usernames):
    """
    Fetches data for multiple LeetCode usernames.
    :param usernames: List of usernames
    :return: A list of user data dictionaries
    """
    results = []
    for username in usernames:
        user_data = fetch_user_data(username)
        results.append(user_data)
    return results

# Step 4: Display Data in a Table Format
def display_data(data):
    """
    Displays user data in a table-like format.
    :param data: List of dictionaries containing user data.
    """
    table = PrettyTable()
    table.field_names = ["Username", "Ranking", "Problems Solved", "Badges"]

    for user in data:
        if "error" in user:
            table.add_row([user["username"], "Error", "-", "-"])
        else:
            table.add_row([
                user["username"],
                user["ranking"] or "N/A",
                user["problems_solved"],
                ", ".join(user["badges"]) if user["badges"] else "None"
            ])

    print(table)

# Main Program Logic
if __name__ == "__main__":
    try:
        # Step 1: Handle input
        usernames = get_usernames()
        print(f"Fetching data for {len(usernames)} users...")

        # Step 2: Fetch user data
        user_data_list = fetch_all_users(usernames)

        # Step 3: Display data
        display_data(user_data_list)
    except Exception as e:
        print(f"Error: {e}")
