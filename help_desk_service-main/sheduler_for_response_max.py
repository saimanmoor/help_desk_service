import requests
import time
import db_working
import config

botToken = config.get_config_data('max_bot')['token']
BASE_URL = 'https://platform-api.max.ru'


def sendMaxMessage(chatId, text, replyToMid=None):
    url = f'{BASE_URL}/messages'
    headers = {
        'Authorization': botToken,
        'Content-Type': 'application/json',
    }
    params = {
        'access_token': botToken,
        'chat_id': chatId,
    }
    payload = {
        'text': text,
    }
    if replyToMid:
        payload['link'] = {
            'type': 'reply',
            'mid': replyToMid,
        }
    response = requests.post(url, headers=headers, params=params, json=payload)
    return response


def getDataAndSendMessage():
    try:
        tickets = db_working.get_tickets_for_send_max()

        for ticket in tickets:
            ticketId = ticket[0]
            chatId = ticket[1]
            messageText = ticket[2] or ''
            maxMessageId = ticket[3]

            if not messageText.strip():
                messageText = 'Ваша заявка закрыта. Спасибо за Ваше обращение.'

            response = sendMaxMessage(chatId, messageText, replyToMid=maxMessageId)

            if response.status_code == 200:
                db_working.update_ticket(ticketId=ticketId, sended=True)
                print(f'[MAX] Ticket {ticketId} response sent to chat {chatId}')
            else:
                print(f'[MAX] Failed to send ticket {ticketId}: {response.status_code} {response.text}')

    except Exception as e:
        print(f'[MAX] Error: {e}')


def sendUnsentMessages():
    """Send unsent messages from ticket conversation to MAX messenger."""
    try:
        messages = db_working.get_unsent_messages_for_max()

        for msg in messages:
            messageId = msg[0]
            ticketId = msg[1]
            chatId = msg[2]
            messageText = msg[3]
            originalMaxMessageId = msg[4]  # max_message_id из сообщения (ссылка на оригинал)
            senderType = msg[5]

            if not messageText.strip():
                db_working.mark_message_sent(messageId)
                continue

            # Получаем оригинальный max_message_id из заявки для ответа
            originalMid = db_working.get_original_message_for_ticket(ticketId)

            response = sendMaxMessage(chatId, messageText, replyToMid=originalMid)

            if response.status_code == 200:
                db_working.mark_message_sent(messageId)
                print(f'[MAX MSG] Message {messageId} from ticket {ticketId} sent to chat {chatId}')
            else:
                print(f'[MAX MSG] Failed to send message {messageId}: {response.status_code} {response.text}')

    except Exception as e:
        print(f'[MAX MSG] Error: {e}')


while True:
    time.sleep(5)
    getDataAndSendMessage()
    sendUnsentMessages()
