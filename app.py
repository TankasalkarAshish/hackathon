import streamlit as st
import requests
import pandas as pd

# Step 1: Input Handling from a .txt file
def get_usernames_from_file(uploaded_file):
    """
    Fetch a list of usernames from the uploaded .txt file.
    """
    try:
        usernames = []
        # Read file content
        content = uploaded_file.getvalue().decode("utf-8")
        # Split the file content into lines and strip any whitespace
        usernames = [line.strip() for line in content.splitlines()]
        
        # Ensure the number of usernames does not exceed 100
        if len(usernames) > 200:
            st.error("The number of usernames cannot exceed 100.")
            return []
        return usernames
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return []

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
            "badges": ", ".join([badge["displayName"] for badge in badges]) if badges else "None"
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

# Step 4: Display Data in Streamlit as a Proper Table
def display_data(data):
    """
    Displays user data in a table format in Streamlit using st.dataframe().
    :param data: List of dictionaries containing user data.
    """
    if data:
        # Convert the list of dictionaries into a pandas DataFrame for better table display
        df = pd.DataFrame(data)

        # Sort by 'ranking' (in ascending order to get the best ranked first)
        df.sort_values(by='ranking', ascending=True, inplace=True)

        # Reset the index and start from 1
        df.reset_index(drop=True, inplace=True)
        df.index += 1  # Set the index to start from 1

        # Display the DataFrame as an interactive table in Streamlit
        st.dataframe(df)
    else:
        st.warning("No data to display.")

# Streamlit Main Logic
def main():
    st.title("LeetCode User Fetcher")

    # Step 1: Upload .txt file with usernames
    uploaded_file = st.file_uploader("Upload a .txt file with LeetCode usernames", type=["txt"])
    
    if uploaded_file is not None:
        # Step 2: Handle file content and get usernames
        usernames = get_usernames_from_file(uploaded_file)

        if usernames:
            st.write(f"Fetching data for {len(usernames)} users...")

            # Step 3: Fetch user data
            user_data_list = fetch_all_users(usernames)

            # Step 4: Display data as a proper table
            display_data(user_data_list)

if __name__ == '__main__':
    main()
