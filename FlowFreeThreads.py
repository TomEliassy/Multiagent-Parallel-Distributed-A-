import Agent
import threading
import sys
import ctypes


threads = {} # A container for the Threads
colorsAndPlayers = {} # Maps between char representation of players to numerical representation

global started_threads # Global counter for counting the custom Threads that are already running
started_threads = 0


##############################################################
# ----------Notifying the Main-Thread Mechanism--------------
##############################################################

class ServiceExit(Exception):
    """
    A custom Exception which is used to trigger the main program about a solution finding.
    """
    pass


def service_shutdown(signum):
    """
    The method which throws the custom exception in order to indicate the Main Thread that a solution was calculated.
    :param signum: The signal for broadcasting the Main Thread
    :return: Raises a ServiceExit (Exception) object
    """
    print('Caught signal %d' % signum)
    raise ServiceExit

############################################################################################
# Global Functions for Starting and Terminating all the FreeFlowThreads in the Threads-pool
############################################################################################

def terminate_threads():
    """
    A method for a clean exit of all the custom running Threads. (Can't be done using Signals for custom Threads,
    only by this mechanism).
    """
    thread_num = 0
    global threads
    for agent_index in Agent.agents:
        threads[thread_num]._stop_event.set()
        threads[thread_num]._is_stopped = True
        print("Terminating " + threads[thread_num].name)
        thread_num += 1

def run_threads():
    """
    A method for starting all the custom Threads which are in the Threads-pool(container).
    """
    thread_num = 0
    global threads
    global started_threads
    for started_threads in Agent.agents:
        threads[started_threads].start()
        started_threads += 1
    started_threads += 1

##############################################################
# ---------------Custom Thread class--------------------------
##############################################################

class FlowFreeThread (threading.Thread):
   """
    A custom Thread class that performs the A* search for the agent that it is identified with.
   """
   def __init__(self, threadID, agent, queue):
      """
      The custom Thread Constructor.
      :param threadID: Thr ID of the identified Agent.
      :param agent: The identified Agent object.
      :param queue: A container for catching the thrown Exceptions
      """
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = " Thread of agent " + str(agent.player_num)
      self.agent = agent
      self._stop_event = threading.Event()
      self.queue = queue

   def run(self):
      """
        A method which performs the code of the Multiagent Parallel Distributed A* FOR THE CURRENT FreeFlowThread.
      """
      Agent.print_mutex.acquire()
      print ("Starting " + self.name) # Atomic printing - without interrupting.
      Agent.print_mutex.release()
      try:
        while not self._stop_event.is_set():
            global colorsAndPlayers , started_threads
            while (started_threads < len(colorsAndPlayers)): # Waits for all the other FreeFlowThreads to be created
                pass
            self.agent.multiagent_astar() # Parallel Distributed Multiagent A*
      except Exception:
        self.queue.put(sys.exc_info())
        print ("Exiting " + self.name)

   def stop(self):
       """
        Stops the current FreeFlowThread.
       """
       self._stop_event.set()

   def stopped(self):
       """
        Returns whether the current FreeFlowThread is stopped.
       """
       return self._stop_event.is_set()

   def get_id(self):
       """
        Returns the ID of the respective FreeFlowThread.
       """
       if hasattr(self, '_thread_id'):
           return self._thread_id
       for id, thread in threading._active.items():
           if thread is self:
               return id

   def raise_exception(self):
       """
        A method for raising an Exception to terminating the current FreeFlowThread.
       """
       thread_id = self.get_id()
       res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                        ctypes.py_object(SystemExit))
       if res > 1: # checks for successfully Exception throwing
           ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
           print('Exception raise failure')
