import os
from dotenv import load_dotenv 
from email.message import EmailMessage
import ssl
import smtplib
from twilio.rest import Client

load_dotenv()

def enviar_email(email, token_value):
    password = os.getenv('password')
    email_sender = 'dylanbatzin@gmail.com'
    email_reciver = email

    subjetc = "Token Cruz Verde"
    body = "Token: " + token_value
    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_reciver
    em['Subject'] = subjetc
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=context) as smtp:
        smtp.login(email_sender,password)
        smtp.sendmail(email_sender,email_reciver,em.as_string())

def enviar_sms(telefono, token_value):
        account_sid =  os.getenv('account_sid')
        auth_token = os.getenv('auth_token')
        client = Client(account_sid, auth_token)

        # Usa el número que verificaste en Twilio como remitente
        twilio_number = '+502 5838 3932	'  # Este es el número que has verificado como remitente

        # Mensaje a enviar
        mensaje = f"Tu código de verificación es: {token_value}"

        # Enviar el mensaje por SMS
        message = client.messages.create(
            body=mensaje,
            from_=twilio_number,  # Número verificado en Twilio como remitente
            to='+502' + telefono  # Número de destino
        )

        print(f"Mensaje enviado con SID: {message.sid}")
