import asyncio


class Controller:
    """
    Class controller, synchronizes the tasks.
    """
    def __init__(self, tasks, loop):
        self._events = []                   # List to save one event to wake up the task, and one event to inform that
        # the task has finished.
        self._finalevent = asyncio.Event()  # The tasks will use this event to wake up the controller
        self._faillist = set()              # Set of failed tasks
        self._skippedlist = set()           # Set of skipped tasks
        self._finishedtasks = set()         # Set of finished tasks
        self._taskslist = tasks             # List of tasks
        self._loop = loop                   # Event loop

    def starttasks(self):
        """
        Adds all the tasks to the event loop.
        :return: None
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self.coordinatetasks())    # Task to coordinate the rest of the tasks
        for task in self._taskslist:
            doneevent = asyncio.Event()     # The task will use this event to inform that it has finished
            if task.hasdependencies():
                waitevent = asyncio.Event()     # The task will wait for this event
                self._events.append([waitevent, doneevent, task])
                loop.create_task(task.executetask(waitevent, doneevent, self._finalevent))  # We create a single
                # process for every task
            else:
                self._events.append([None, doneevent, task])    # The task does not have to wait, no dependencies
                loop.create_task(task.executetask(None, doneevent, self._finalevent))
        loop.run_forever()

    def printresults(self):
        """
            This function print the result of the tasks
        """
        print()
        for t in self._finishedtasks:
            print(t + " OK")
        for t in self._faillist:
            print(t + " FAILED")
        for t in self._skippedlist:
            print(t + " SKIPPED")

    async def coordinatetasks(self):
        """
        Sends a signal to the tasks if they can execute.
        Saves the status of a ended task.
        :return: None
        """
        ended = 0   # Number of ended tasks
        while ended < len(self._taskslist):
            await self._finalevent.wait()   # Wait until one task finish
            for event in self._events:
                if event[1].is_set():       # If this task has finished we save the status
                    if event[2].getstatus() == "ok":
                        self._finishedtasks.add(event[2].getname())
                    elif event[2].getstatus() == "skip":
                        self._skippedlist.add(event[2].getname())
                    elif event[2].getstatus() == "fail":
                        self._faillist.add(event[2].getname())
                    self._events.remove(event)
                    ended += 1
            for event in self._events:
                if event[2].hasdependencies():
                    if event[2].getdependencies().issubset(self._finishedtasks):
                        event[0].set()  # If all the dependencies are done, we send a signal to start the task
                    elif len(event[2].getdependencies().intersection(self._faillist)) > 0 \
                            or len(event[2].getdependencies().intersection(self._skippedlist)) > 0:
                        self._skippedlist.add(event[2].getname())
                        self._events.remove(event)
                        ended += 1
            self._finalevent.clear()    # Resets the signal, the controller will wait again until another task ends

        for task in asyncio.Task.all_tasks():   # Cancel all the skipped tasks
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print("Cancelled task without finishing.")
        self._loop.stop()


