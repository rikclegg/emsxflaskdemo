#!/usr/bin/env python

import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from easymsx.easymsx import EasyMSX
from easymsx.notification import Notification

class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(block_start_string='$$',
                              block_end_string='$$',
                              variable_start_string='$',
                              variable_end_string='$',
                              comment_start_string='$#',
                              comment_end_string='#$'
                              ))

def process_notification(notification):
    print("EasyMSX notification received...")
    socketio.emit("emsxevent","EasyMSX Notification received",namespace="/emsx")
    #socketio.sleep(1)

emsx = EasyMSX()
emsx.add_notification_handler(process_notification)

app = CustomFlask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create', namespace="/emsx")
def on_create(data):
    print("Connected...")
    emsx.start()


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

    socketio.run(app, debug=True)
