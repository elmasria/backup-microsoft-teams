import json
import os
from string import Template

from dotenv import load_dotenv

from authenticator import Authenticator
from image_parser import ImageSrcParser
from utils import (add_attachment_links_to_content, fetch_attachments,
                   get_chats, get_message_metadata, get_messages, get_user_id,
                   handle_images)

load_dotenv()

# os.makedirs('export/images', exist_ok=True)

parser = ImageSrcParser()

chat_id =os.getenv('chat_id')

authenticator = Authenticator('auth/token.js')
azure = authenticator.authenticate()

my_id = get_user_id(azure)

chats = list(get_chats(azure))
# with open('chats.json', 'w') as file:
#     json.dump(chats, file)

response_messages = None

folder_name = os.getenv('folder_name')

os.makedirs(f'{folder_name}/export/images', exist_ok=True)

with open(f'{folder_name}/chat.html', 'w', encoding='utf-8') as output_file:
    with open('html/header.html', 'r', encoding='utf-8') as header_file:
        output_file.write(header_file.read())

    with open('html/message_template.html', 'r', encoding='utf-8') as template_file:
        message_template = Template(template_file.read())

    for message, timestamp in get_messages(azure, chat_id):
        parser.clear()

        sender, sender_id, css_class = get_message_metadata(message, my_id)
        attachment_filenames = fetch_attachments(azure, chat_id, message['id'], folder_name)


        content = message['body']['content']
        parser.feed(content)
        content = handle_images(parser, azure, content, folder_name)
        content = add_attachment_links_to_content(attachment_filenames, content)

        data = {
            'css_class': css_class,
            'sender': sender,
            'content': content,
            'timestamp': timestamp,
        }

        message_output = message_template.substitute(data)

        output_file.write(message_output)

    with open('html/footer.html', 'r', encoding='utf-8') as footer_file:
        output_file.write(footer_file.read())



