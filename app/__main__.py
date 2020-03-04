import json
import jsonschema
from jsonschema import validate
import asyncio

from controller.controller import Controller
from model.task import Task


def createtasks(tasklistinput):
    """
    Creates one class Task for every task in the input file.
    :param tasklistinput: Tasks from the input file.
    :return: List of classes Task.
    """
    tasklist = []
    for taskinput in tasklistinput:
        if "dependencies" in taskinput:
            task = Task(taskinput["name"], taskinput["type"], taskinput["arguments"], taskinput["dependencies"])
        else:
            task = Task(taskinput["name"], taskinput["type"], taskinput["arguments"], None)
        tasklist.append(task)
    return tasklist


def readfile():
    """
        This function read the input file and save the data in the list "taskslist"
    """
    with open('../resources/schema.json') as json_file:  # Loads the schema
        schema = json.load(json_file)
    with open('../resources/input1.json') as json_file:
        taskslist = json.load(json_file)    # Loads the data
        try:
            validate(taskslist, schema)     # Checks the data with the schema
        except jsonschema.exceptions.ValidationError as ve:
            print("Record #{}: ERROR\n")
    return taskslist


def __main__():
    """
        Main function, creates the loop and starts the controller class.
    """
    taskslist = readfile()
    tasks = createtasks(taskslist["tasks"])
    loop = asyncio.get_event_loop()
    controller = Controller(tasks, loop)
    controller.starttasks()
    controller.printresults()
    loop.close()


__main__()


