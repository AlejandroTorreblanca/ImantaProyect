import asyncio
import sys

from controller.controller import Controller


class Task:
    """
    Class Task, represents a task which we want to execute.
    """
    def __init__(self, name, tasktype, arguments, dependencies):
        self.__name = name               # Name of the task
        self.__type = tasktype           # Type of the task
        self.__arguments = arguments     # Arguments of the task
        if dependencies is not None and len(dependencies) > 0:
            self.__dependencies = set()  # Dependencies of the task
            for dep in dependencies:
                self.__dependencies.add(dep)
        else:
            self.__dependencies = None
        self.__taskstatus = "waiting"    # Status of the task, when the task ends it can be "ok", "fail" or "skip"

    def getname(self):
        """
        Gets the name of the task
        :return: Task's name
        """
        return self.__name

    def getstatus(self):
        """
        Gets the status of the task
        :return: Task's status
        """
        return self.__taskstatus

    def getdependencies(self):
        """
        Gets the dependencies of the task
        :return: Task's dependencies
        """
        return self.__dependencies

    def hasdependencies(self):
        """
        Checks if the task has dependencies
        :return: True if the task has dependencies, false in other case
        """
        if self.__dependencies is not None:
            return True
        return False

    async def executetask(self, depencencesevent, finalevent):
        """
        This function execute the task arguments
        :return: None
        """
        print("Started " + self.__name)          # The task starts
        if depencencesevent is not None:
            await depencencesevent.wait()
        if self.__type == "exec":    # The task has shell commands
            try:
                proc = await asyncio.create_subprocess_shell(
                    self.__arguments, stdout=asyncio.subprocess.PIPE)    # Execute the shell commands
                await proc.wait()                                       # Wait until the instruction ends
                if proc.returncode != 0:            # If the return code is not 0 we set the task as failed
                    self.__taskstatus = "fail"
                else:
                    lines = (await proc.communicate())[0].splitlines()
                    for line in lines:
                        print(line.strip())
                    self.__taskstatus = "ok"
            except Exception as e:
                print(e)
                self.__taskstatus = "fail"
        else:                           # The task has code snippet
            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, '-c', self.__arguments,
                    stdout=asyncio.subprocess.PIPE)             # Execute the task code
                await proc.wait()                               # Wait until the instruction ends
                lines = (await proc.communicate())[0].splitlines()
                for line in lines:
                    print(line.strip())
                self.__taskstatus = "ok"
            except Exception as e:
                print(e)
                self.__taskstatus = "fail"
        print("Ended " + self.__name)
        Controller.getinstance().sendmessage([self.__name, self.__taskstatus])  # Informs that the current task is done
        finalevent.set()                # Wakes up the controller

