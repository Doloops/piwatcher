import redis
import threading
import time

def backgroundSubscribe ():
    print("Hello")
    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    p = r.pubsub()
    p.subscribe("mynews")
    
    for message in p.listen():
        print("New message : " + str(message))
        if message["type"] == "message":
            print ("data : " + message["data"] + " [" + str(type(message["data"]))+ "]")
        
    print ("Leaving thread now !")
    
thread = threading.Thread(target=backgroundSubscribe, args=())
thread.start()

time.sleep(0.1)
    
r = redis.StrictRedis(host='localhost', port=6379, db=0)

r.publish("mynews", "New from python !")

fl=45.85
r.publish("mynews", fl)
