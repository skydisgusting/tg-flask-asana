import time
from threading import Thread

import asana
import hashlib
import hmac
import json
import logging
import os
import requests
import sys
import threading
from asana.error import AsanaError
from dotenv import load_dotenv
from flask import Flask, request, make_response, url_for, redirect, flash
from urllib.parse import urlencode

import functions as func

load_dotenv()

workspace = os.getenv('ASANA_WORKSPACE')
token = os.getenv('TELEGRAM_TOKEN')

client = asana.Client.oauth(
    client_id=os.getenv('ASANA_CLIENT_ID'),
    token=os.getenv('ASANA_CLIENT_SECRET')
)

(url, state) = client.session.authorization_url()

client.options['client_name'] = "Webhook testing"

app = Flask("Webhook inspector")
app.logger.setLevel(logging.INFO)
os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'
app.config['SECRET_KEY'] = 'asdasdasd'
app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)

app.config['OAUTH2_PROVIDER'] = {
    'asana': {
        'client_id': os.getenv("CLIENT_ID"),
        'client_secret': os.getenv("CLIENT_SECRET"),
        'authorize_url': 'https://app.asana.com/-/oauth_authorize/',
        'redirect_uri': 'https://71f2-5-16-97-185.ngrok-free.app/callback/asana',
        'token_url': 'https://app.asana.com/-/oauth_token'
    }
}

ngrok_subdomain = sys.argv[1]


class CreateWebhookThread(threading.Thread):
    def __init__(self, project):
        super().__init__()

        self.project = project

    def run(self):
        webhook = client.webhooks.create(resource=self.project,
                                         fields=["due_on"],
                                         target="https://{0}.ngrok-free.app/receive-webhook?project={1}"
                                         .format(ngrok_subdomain, self.project))


class CreateDeadlineThread(threading.Thread):
    def run(self):
        deadline_handle = func.handle_deadline(client=client)
        for key, value in deadline_handle.items():
            if value.seconds < 86400 and value.days >= 0:
                if value.seconds < 3600 and value.days == 0:
                    deadline_telegram_request('sendMessage',
                                              f'🔥🔥🔥 Задача {key} осталось {value.seconds} секунд!')
                else:
                    deadline_telegram_request('sendMessage', f'Задача {key} осталось {value.seconds} секунд.')
            else:
                deadline_telegram_request('sendMessage', f'Задача {key} просрочена.')

        time.sleep(30)


def deadline_telegram_request(method, data):
    response = requests.post(
        url='https://api.telegram.org/bot{0}/{1}'.format(token, method),
        data={'chat_id': 914040982, 'text': data}
    ).json()

    return response


create_deadline_handle = CreateDeadlineThread()


def get_all_webhooks():
    webhooks = list(client.webhooks.get_all(workspace=os.getenv("ASANA_WORKSPACE")))
    app.logger.info("All webhooks for this pat: \n" + str(webhooks))

    return webhooks


@app.route("/authorize/<provider>")
def oauth2_authorize(provider):
    data = request.get_json()
    user_id = data['user_id']

    app.logger.info(data)

    provider_data = app.config['OAUTH2_PROVIDER'].get(provider)
    if provider_data is None:
        app.logger.error('provider not found 404')
        flash('404 provider not found')

    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': 'https://71f2-5-16-97-185.ngrok-free.app/callback/asana',
        'response_type': 'code',
        'state': data['oauth2_state'],
    })

    return provider_data['authorize_url'] + '?' + qs


@app.route("/callback/<provider>")
def oauth2_callback(provider):
    session = flask.session
    callback_state = request.args['state']
    provider_data = app.config['OAUTH2_PROVIDER'].get(provider)
    if provider_data is None:
        app.logger.error('provider not found 404')

    if 'error' in request.args:
        for k, v in request.args.values():
            if k.startswith('error'):
                flash(f'{k}: {v}')
        return redirect(url_for('index'))

    if request.args['state'] != session.get('oauth2_state'):
        app.logger.error('state not valid 401')

    if 'code' not in request.args:
        app.logger.error('no code 401')

    response = requests.post(provider_data['token_url'],
                             data={
                                 'client_id': provider_data['client_id'],
                                 'client_secret': provider_data['client_secret'],
                                 'code': request.args['code'],
                                 'grant_type': 'authorization_code',
                                 'redirect_uri': 'https://71f2-5-16-97-185.ngrok-free.app/callback/asana',

                             }, headers={'Accept': 'application/json'})

    if response.status_code != 200:
        app.logger.error('response not 200')

    oauth2_token = response.json().get('access_token')
    if not oauth2_token:
        app.logger.error('no token 401')

    return redirect(f'https://google.com/search?q={oauth2_token}')


@app.route("/create_webhook", methods=["GET"])
def create_hook():
    global create_deadline_handle

    webhooks = get_all_webhooks()
    if len(webhooks) != 0:
        return "Hooks already created: " + str(webhooks)

    for project in client.projects.get_projects({'workspace': workspace}):
        create_webhook = CreateWebhookThread(project['gid'])
        create_webhook.start()

    create_deadline_handle.start()
    return """<html>
    <head>
      <meta http-equiv=\"refresh\" content=\"10;url=/all_webhooks\" />
    </head>
    <body>
        <p>creating hook</p>
    </body>"""


@app.route("/all_webhooks", methods=["GET"])
def show_all_webhooks():
    return """<p>""" + str(get_all_webhooks()) + """</p><br />
    <a href=\"/create_webhook\">create_webhook</a><br />
    <a href=\"/remove_all_webhooks\">remove_all_webhooks</a>"""


@app.route("/remove_all_webhooks", methods=["GET"])
def teardown():
    retries = 5
    while retries > 0:
        webhooks = get_all_webhooks()
        if len(webhooks) == 0:
            return "No webhooks"
        for hook in webhooks:
            try:
                app.logger.info(hook)
                client.webhooks.delete_by_id(hook[u"gid"])
                return "Deleted " + str(hook[u"gid"])
            except AsanaError as e:
                print("Caught error: " + str(e))
                retries -= 1
                print("Retries " + str(retries))
        return ":( Not deleted. The webhook will die naturally in 7 days of failed delivery. :("


hook_secret = {}


@app.route("/receive-webhook", methods=["POST"])
def receive_webhook():
    global hook_secret

    project_gid = dict(request.args)['project']
    contents = json.loads(request.data)
    make_request(contents, "sendMessage", client)

    if "X-Hook-Secret" in request.headers:
        app.logger.info("New webhook")
        response = make_response("", 200)
        hook_secret[project_gid] = request.headers["X-Hook-Secret"]
        response.headers["X-Hook-Secret"] = request.headers["X-Hook-Secret"]

        return response

    elif "X-Hook-Signature" in request.headers:

        encoded_hook = hook_secret[project_gid].encode('utf-8', 'ignore')
        signature = hmac.new(encoded_hook, msg=request.data, digestmod=hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature.encode('utf-8', 'ignore'),
                                   request.headers["X-Hook-Signature"].encode('ascii', 'ignore')):
            app.logger.warning("Calculated digest does not match digest from API. This event is not trusted.")
            return
        app.logger.info("Received payload of %s events", len(contents["events"]))
        return ""
    else:
        raise KeyError


def make_request(some_data, method, client_obj):
    data = func.handle_data(request_data=some_data, client=client_obj)

    response = requests.post(
        url='https://api.telegram.org/bot{0}/{1}'.format(token, method),
        data={'chat_id': 914040982, 'text': data}
    ).json()

    return response


if __name__ == "__main__":
    app_thread = Thread(target=app.run(port=int(sys.argv[2]), debug=True, threaded=True))
    app_thread.start()
