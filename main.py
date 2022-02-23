import pika
import sys
from process_image import process_image

# Constaints
exchange = "mea-capture"
route_key = "crop"
durable = True

# Create connection
credentials = pika.PlainCredentials('user', 'password')
parameters = pika.ConnectionParameters(host='localhost',
                                       port=8070,
                                       credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Create exchange
channel.exchange_declare(
    exchange=exchange, exchange_type='topic', durable=durable)

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
