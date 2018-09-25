#!/usr/bin/env python

import gevent
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from easymsx.easymsx import EasyMSX
from easymsx.notification import Notification
from threading import Lock
import json

class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(block_start_string='^^',
                              block_end_string='^^',
                              variable_start_string='^',
                              variable_end_string='^',
                              comment_start_string='^#',
                              comment_end_string='#^'
                              ))

def background_thread():
    global emsx
    emsx = EasyMSX()
    emsx.orders.add_notification_handler(process_order_notification)
    emsx.routes.add_notification_handler(process_route_notification)
    emsx.start()


def process_order_notification(notification):
    print("EasyMSX Order notification received...")
    # build object containing the message data...
    data=[]
    keyset=False
    for fc in notification.field_changes:
        data.append({"name":fc.field.name(),"old_value":fc.old_value,"new_value":fc.new_value})
        if fc.field.name()=="EMSX_SEQUENCE": keyset=True
    
    if not keyset:
        data.append({"name":"EMSX_SEQUENCE","old_value":notification.source.sequence,"new_value":notification.source.sequence})
    
    if notification.type == Notification.NotificationType.INITIALPAINT:
        notification_event = "emsx-order-init"
    elif notification.type == Notification.NotificationType.NEW:
        notification_event = "emsx-order-new"
    elif notification.type == Notification.NotificationType.UPDATE:
        notification_event = "emsx-order-update"
    elif notification.type == Notification.NotificationType.DELETE:
        notification_event = "emsx-order-delete"

    socketio.emit(notification_event,data,namespace="/emsx")
    socketio.sleep(0)

def process_route_notification(notification):
    print("EasyMSX Route notification received...")
    # build object containing the message data...
    data=[]
    keyset=False
    for fc in notification.field_changes:
        data.append({"name":fc.field.name(),"old_value":fc.old_value,"new_value":fc.new_value})
        if fc.field.name()=="EMSX_SEQUENCE": keyset=True
    
    if not keyset:
        data.append({"name":"EMSX_SEQUENCE","old_value":notification.source.sequence,"new_value":notification.source.sequence})
        data.append({"name":"EMSX_ROUTE_ID","old_value":notification.source.route_id,"new_value":notification.source.route_id})
        #print("Data: " +json.dumps(data))

    if notification.type == Notification.NotificationType.INITIALPAINT:
        notification_event = "emsx-route-init"
    elif notification.type == Notification.NotificationType.NEW:
        notification_event = "emsx-route-new"
    elif notification.type == Notification.NotificationType.UPDATE:
        notification_event = "emsx-route-update"
    elif notification.type == Notification.NotificationType.DELETE:
        notification_event = "emsx-route-delete"

    socketio.emit(notification_event,data,namespace="/emsx")
    socketio.sleep(0)

app = CustomFlask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app,async_mode = "gevent")
#socketio = SocketIO(app,async_mode = None)

thread = None
thread_lock = Lock()


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.on('create', namespace="/emsx")
def on_create(data):
    global thread
    print("Connected...")
    with thread_lock:
        if not thread is None:
            thread=None
        thread = socketio.start_background_task(target=background_thread)

@socketio.on('get_teamlist', namespace="/emsx")
def teamlist():
    teamlist=[]
    for team in emsx.teams:
        teamlist.append(team.name)
    print("TeamList: " + ', '.join(teamlist))
    emit("teamlist", teamlist, namespace="/emsx")

@socketio.on('get_brokerlist', namespace="/emsx")
def brokerlist():
    brokerlist=[]
    for broker in emsx.brokers:
        brokerlist.append(broker.name)
    print("BrokerList: " + ', '.join(brokerlist))
    emit("brokerlist", brokerlist, namespace="/emsx")
    

if __name__ == '__main__':
    gevent.get_hub()
    socketio.run(app, debug=True)
