import keys
from twilio.rest import Client


def send_sms(to_number, message):

    to_number = to_number if to_number.startswith('+20') else '+20' + to_number[1:]

    print(f"Sending SMS to {to_number}")

    client = Client(keys.account_sid, keys.auth_token)

    message = client.messages.create(
        body=message,
        from_=keys.twilio_number,
        to=to_number
    )

    return True, message.sid