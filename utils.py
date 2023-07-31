import os
import uuid

from dateutil.parser import parse


def format_date(date_string):
    # Convert the date string to a datetime object
    dt = parse(date_string)

    # Format the datetime object to the desired format
    formatted_date = dt.strftime('%m/%d/%y %I:%M %p')

    return formatted_date


def get_user_id(session):
    response = session.get('https://graph.microsoft.com/v1.0/me')
    if response.status_code == 200:
        profile = response.json()
        user_id = profile.get('id', 'User id not found')
        if user_id == 'User id not found':
            print("User id not found in response. The response was:")
            print(profile)
        else:
            print(f"User id: {user_id}")
            return user_id
    else:
        print(f"Failed to get profile, status code: {response.status_code}")
        print(response.content)
    return None

def get_chats_list(azure):
    response = azure.get('https://graph.microsoft.com/v1.0/me/chats')
    chats_list = response.json()
    return chats_list['value']

def get_chats(azure):
    response_chats = None

    while True:
        if response_chats is None:
            response_chats = azure.get('https://graph.microsoft.com/v1.0/me/chats')
        else:
            # On subsequent iterations, check for the @odata.nextLink to get the next page of chats
            if '@odata.nextLink' in response_chats:
                chat_url = response_chats['@odata.nextLink']
                response_chats = azure.get(chat_url)
            else:
                # If there is no nextLink, exit the loop
                break

        chats = response_chats.json()
        print(len(chats['value']))
        # Yield each chat
        for chat in chats['value']:
            yield chat


def get_messages(azure, chat_id):
    response_messages = None
    messages = None
    totalMessages = 0

    while True:
        if response_messages is None:
            response_messages = azure.get(f"https://graph.microsoft.com/v1.0/me/chats/{chat_id}/messages?$top=50")
        else:
            if messages is not None and '@odata.nextLink' in messages:
                chat_url = messages['@odata.nextLink']
                response_messages = azure.get(chat_url)
            else:
                break

        messages = response_messages.json()
        totalMessages += len(messages['value'])
        print(totalMessages)
        for message in messages['value']:
            created_datetime = message['createdDateTime']
            formatted_date = format_date(created_datetime)
            yield message, formatted_date


def get_message_metadata(message, my_id):
    """Return sender's name, ID and CSS class based on the given message and user's ID."""
    if message['from'] is not None and message['from']['user'] is not None:
        sender = message['from']['user']['displayName']
        sender_id = message['from']['user']['id']
    else:
        sender = "Unknown Sender"
        sender_id = None

    css_class = "right" if sender_id == my_id else "left"

    return sender, sender_id, css_class

def fetch_attachments(azure, chat_id, message_id, folder_name):
    """Fetches and saves all attachments of the given message and returns a list of their filenames."""
    attachments = None
    filenames = []
    attachments_url = f"https://graph.microsoft.com/v1.0/me/chats/{chat_id}/messages/{message_id}/attachments"
    response_attachments = azure.get(attachments_url)
    if response_attachments.status_code == 200:
        attachments = response_attachments.json()['value']
        for attachment in attachments:
            content_url = attachment['contentUrl']
            fname_with_folder = f"{folder_name}/export/attachment/{attachment['id']}.{attachment['name'].split('.')[-1]}"  # Use the attachment's ID and original extension for the filename
            filename = f"export/attachment/{attachment['id']}.{attachment['name'].split('.')[-1]}"
            response = azure.get(content_url, stream=True)
            if response.status_code == 200:
                with open(fname_with_folder, 'wb') as f:
                    for chunk in response:
                        f.write(chunk)
            filenames.append(filename)
    return filenames

def add_attachment_links_to_content(attachment_filenames, content):
    if attachment_filenames:
        content += '<br>Attachments:<br>'
        for filename in attachment_filenames:
            attachment_name = os.path.basename(filename)
            content += f'<a href="{filename}">{attachment_name}</a><br>'
    return content


def handle_images(parser, azure, content, folder_name):
    if hasattr(parser, 'img_src') and parser.img_src is not None:
        filename = []

        if len(parser.img_src) != len(parser.item_id):
            # Append enough UUIDs to parser.item_id to make its length equal to the length of parser.img_src
            parser.item_id.extend(str(uuid.uuid4()) for _ in range(len(parser.img_src) - len(parser.item_id)))

        for i in range(len(parser.img_src)):
            img_url = parser.img_src[i]
            fname_with_folder = f'{folder_name}/export/images/{parser.item_id[i]}.jpeg'
            fname = f'export/images/{parser.item_id[i]}.jpeg'
            filename.append(fname)
            if not os.path.exists(fname_with_folder):
                response = azure.get(img_url, stream=True)
                if response.status_code == 200:
                    with open(fname_with_folder, 'wb') as img_file:
                        for chunk in response:
                            img_file.write(chunk)

        content = parser.replace_img_src(content, filename)

    return content
