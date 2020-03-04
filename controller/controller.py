import asyncio


class Controller:
    """
    Class controller, Singleton pattern, synchronizes the tasks.
    """
    __instance = None

    @staticmethod
    def getinstance():
        """
        Static access method to get the instance oh the controller.
        :return: Unique instance of the controller class
        """
        if Controller.__instance is None:
            Controller()
        return Controller.__instance

    def __init__(self):
        """
        Virtually private constructor.
        """
        if Controller.__instance is not None:
            raise Exception("The class Controller is a singleton, you must get the instance using 'getinstance()'")
        else:
            Controller.__instance = self
            self.__events = []      # List to save one event for every task, use this event to wake up the task
            self.__messages = []    # List of messages of the finished tasks
            self.__finalevent = asyncio.Event()     # The tasks will use this event to wake up the controller
            self.__faillist = set()                 # Set of failed tasks
            self.__skippedlist = set()              # Set of skipped tasks
            self.__finishedtasks = set()            # Set of finished tasks
            self.__taskslist = None                 # List of tasks
            self.__loop = asyncio.get_event_loop()  # Event loop

    def sendmessage(self, message):
        """
        Tasks will use this function to report the status, adds the message to the list of messages
        :param message: List of tow elements, first the name of the task and second the status
        :return: None
        """
        self.__messages.append(message)

    def end(self):
        """
        Ends the loop before close the application
        :return: None
        """
        self.__loop.close()

    def starttasks(self, tasks):
        """
        Adds all the tasks to the event loop.
        :return: None
        """
        self.__taskslist = tasks
        self.__loop.create_task(self.coordinatetasks())    # Task to coordinate the rest of the tasks
        for task in self.__taskslist:
            if task.hasdependencies():
                waitevent = asyncio.Event()     # The task will wait for this event
                self.__events.append([waitevent, task])
                self.__loop.create_task(task.executetask(waitevent, self.__finalevent))  # We create a single
                # process for every task
            else:
                self.__loop.create_task(task.executetask(None, self.__finalevent))
        self.__loop.run_forever()

    def printresults(self):
        """
            Prints the result of the tasks
        """
        print()
        for t in self.__finishedtasks:
            print(t + " OK")
        for t in self.__faillist:
            print(t + " FAILED")
        for t in self.__skippedlist:
            print(t + " SKIPPED")

    async def coordinatetasks(self):
        """
        Sends a signal to the tasks if they can execute.
        Saves the status of a ended task.
        :return: None
        """
        ended = 0   # Number of ended tasks
        while ended < len(self.__taskslist):
            await self.__finalevent.wait()   # Wait until one task finish
            for message in self.__messages:
                if message[1] == "ok":
                    self.__finishedtasks.add(message[0])
                elif message[1] == "skip":
                    self.__skippedlist.add(message[0])
                elif message[1] == "fail":
                    self.__faillist.add(message[0])
                self.__messages.remove(message)
                ended += 1
            for event in self.__events:     # Checks if some task can start or if some task should be skipped
                if event[1].getdependencies().issubset(self.__finishedtasks):
                    event[0].set()  # If all the dependencies are done, we send a signal to start the task
                    self.__events.remove(event)
                elif len(event[1].getdependencies().intersection(self.__faillist)) > 0 \
                        or len(event[1].getdependencies().intersection(self.__skippedlist)) > 0:
                    self.__skippedlist.add(event[1].getname())
                    self.__events.remove(event)
                    ended += 1
            self.__finalevent.clear()    # Resets the signal, the controller will wait again until another task ends

        for task in asyncio.Task.all_tasks():   # Cancels all the skipped tasks
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print("Cancelled task without finishing.")
        self.__loop.stop()



