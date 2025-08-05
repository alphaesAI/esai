import os
import yaml

from multiprocessing.pool import ThreadPool

from ..pipeline import PipelineFactory
from ..workflow import WorkflowFactory

class Application:
    @staticmethod
    def read(data):
        if isinstance(data, str):
            if os.path.exists(data):
                with open(data, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)                    #parse the yaml content into dict
            
            data = yaml.safe_load(data)
            if not isinstance(data, str):
                return data
            
            raise FileNotFoundError(f"unable to load the file: '{data}'")
        
        return data
    
    def __init__(self, config, loadata=True):
        self.config = Application.read(config)
        self.pool = None

        self.createpipelines()
        self.createworkflows()


    def createpipelines(self):
        self.pipelines = {}

        pipelines = list(PipelineFactory.list().keys())             #default pipelines

        for key in self.config:
            if "." in key:                                          # custom pipelines
                pipelines.append(key)

        for pipeline in pipelines:
            if pipeline in self.config:
                config = self.config[pipeline] if self.config[pipeline] else {}

                self.pipelines[pipeline] = PipelineFactory.create(config, pipeline)

    def createworkflows(self):
        """
        reads the yaml file, creates workflow instances.
        scheduling the tasks if it's defined.


        config = {"tasks"" [ {"action": "tabular"}]}
        config["tasks"] = [{"action": "tabular"}]
        """

        self.workflows = {}

        if "workflow" in self.config:
            for workflow, config in self.config["workflow"].items():
                config = config.copy()

                config["tasks"] = [self.resolvetask(task) for task in config["tasks"]]

                schedule = config.pop("schedule", None)

                self.workflows[workflow] = WorkflowFactory.create(config, workflow)         #workflow: workflow name
                #now it becomes instance of the workflow

                if schedule:
                    if not self.pool:
                        self.pool = ThreadPool()
                    
                    self.pool.apply_async(self.workflows[workflow].schedule, kwds=schedule) #workflow instance calls the schedule method and pass the schedule info

    def resolvetask(self, task):
        """
        we pass the task as an input and 
        return the task as a callable object dictionary
        args: {"action": "tabular"}
        returns: {"action": <tabualr object>}

        task = {"action": "tabular"}
        action = "tabular"
        values = ["tabular"]
        actions = [Tabular()]
        """
        task = {"action": task} if isinstance(task, (str, list)) else task   #we need dict form: {"action": "tabular"}

        if "action" in task:
            action = task["action"]
            values = [action] if not isinstance(action, list) else action

            actions = []
            for a in values:
                actions.append(self.function(a))
            
            task["action"] = actions[0] if not isinstance(action, list) else actions        #return the values in their original form

        return task
    
    def function(self, function):
        """
        return the function as callable object.

        function: values from resolvetask

        if the value is not in pipeline and workflow, we have to create it.
        """
        if function in self.pipelines:
            return self.pipelines[function]     # callable object
        
        if function in self.workflows:
            return self.workflows[function]
        
        return PipelineFactory.create({}, function)

    def pipeline(self, name, *args, **kwargs):
        args = args[0] if args and len(args) == 1 and isinstance(args[0], tuple) else args
        
        if name in self.pipelines:
            return self.pipelines[name](*args, **kwargs)
        
        return None
    
    def workflow(self, name, elements):
        """
        we're passing workflow name and inputs.
        
        """
        if hasattr(elements, "__len__") and hasattr(elements, "__getitem__"):
            elements = [tuple(element) if isinstance(element, list) else element for element in elements]
        else:
            elements = (tuple(element) if isinstance(element, list) else element for element in elements)

        return self.workflows[name](elements)
    
    def wait(self):
        """
        Closes threadpool and waits for completion.
        """

        if self.pool:
            self.pool.close()
            self.pool.join()
            self.pool = None
