from keys import SLACK_ID
from slackclient import SlackClient

name = 'sjakkbot'
slack_client = SlackClient(SLACK_ID)

if __name__ == "__main__":
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == name:
                print("ID: %s" % user.get('id'))
    else:
        print("Could not find %s" % name)
