from asana import Client
import os
import time
import datetime
import re

workspace = os.getenv('ASANA_WORKSPACE')


def task_completed(task_gid, client):
    output = " "
    task = client.tasks.find_by_id(task_gid)

    task_complete = task["completed"]
    task_name = task["name"]

    if task_complete is True:
        output = f'Задача "{task_name}" изменила статус на "✅ Завершена"'

    if task_complete is False:
        output = f'Задача "{task_name}" изменила статус на "❌ Не завершена"'

    return output


def handle_deadline(client: Client):
    time.sleep(10)
    output = {}
    for project in client.projects.get_projects({'workspace': workspace}):
        for task in client.tasks.get_tasks({"project": project['gid']}):
            task_id = client.tasks.find_by_id(task['gid'])
            task_deadline = task_id['due_at']

            if task_deadline:
                task_date = re.split(r'[T:-]', task_deadline)
                year = int(task_date[0])
                month = int(task_date[1])
                day = int(task_date[2])
                hour = int(task_date[3])
                minute = int(task_date[4])
                second = int(task_date[5][:-5])

                task_datetime = datetime.datetime(year, month, day, hour, minute, second)
                now_datetime = datetime.datetime.utcnow()
                now_datetime.replace(microsecond=0)

                left_datetime = task_datetime - now_datetime

                output[task_id['gid']] = left_datetime

    return output


def handle_data(request_data, client: Client):
    try:
        task_gid = request_data['events'][0]['resource']['gid']
        task_field = request_data['events'][0]['change']['field']
        task_action = request_data['events'][0]['change']['action']

        if task_field == "completed" and task_action == "changed":
            return task_completed(task_gid=task_gid, client=client)

    except KeyError:
        print('Empty Handle')
    except Exception as e:
        print("Unexpected error", e)


def get_key(data, value):
    for k, v in data.items():
        if v == value:
            return k
