import pika
import sys
import os
from process_image import process_image
from dotenv import load_dotenv

# take environment variables from .env.
load_dotenv()

# Constaints
exchange = os.getenv.get("RABBITMQ_EXCHNAGE", "mea-capture")
route_key = os.getenv.get("RABBITMQ_ROUTE_KEY", "crop")
durable = os.getenv.get("RABBITMQ_DURABLE", "true") == "true"

# Create connection
credentials = pika.PlainCredentials(
    os.getenv.get("RABBITMQ_USER", "user"),
    os.getenv.get("RABBITMQ_PASSWORD", "password"))
parameters = pika.ConnectionParameters(host=os.getenv.get("RABBITMQ_HOST", "localhost"),
                                       port=int(os.getenv.get(
                                           "RABBITMQ_PORT", "5672")),
                                       credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Create exchange
channel.exchange_declare(exchange=exchange,
                         exchange_type=os.getenv.get("RABBITMQ_EXCHNAGE_TYPE", "fanout"), durable=durable)

# Create queue
result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue

# Bind queue to channels
channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=route_key)


# Shutdown
def shutdown():
    print("EXIT SIGNAL")
    channel.close()
    sys.exit(0)


# Listener callback
def callback(ch, method, properties, body):
    body = body.decode("utf-8")
    print(" [x] %r:%r" % (method.routing_key, body))

    # EXIT
    if body == "EXIT":
        shutdown()
    else:
        process_image(body)


# Start listening
print(' [*] Waiting for logs. To exit press CTRL+C')
channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()
