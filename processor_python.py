import json
from typing import List, Dict

import dotenv
import requests
from RestrictedPython import compile_restricted, safe_globals, utility_builtins
from RestrictedPython.Eval import default_guarded_getitem, default_guarded_getiter
from RestrictedPython.Guards import full_write_guard, safer_getattr, guarded_iter_unpack_sequence, guarded_setattr
from core.base_message_router import Router
from core.base_model import ProcessorState
from core.base_processor import BaseProcessor
from core.processor_state import StateConfigCode, State
from core.processor_state_storage import StateMachineStorage

from tenacity import retry, wait_exponential, wait_random, retry_if_not_exception_type
from logger import log

dotenv.load_dotenv()
logging = log.getLogger(__name__)


# base class for runnable python scripts that take query inputs and expect outputs
class BaseRunnable:
    def __init__(self,
                 output_state: State,
                 storage: StateMachineStorage,
                 **kwargs):

        self.storage = storage
        self.output_state = output_state
        self.properties = {}

        super().__init__()

    def process_query_states(self, query_states: List[Dict]) -> List[Dict]:
        raise NotImplementedError()


class PythonProcessor(BaseProcessor):

    def create_runnable_class_instance(self) -> BaseRunnable:
        new_class_content = self.template

        # Compile the restricted code
        compiled_code = compile_restricted(new_class_content, '<string>', 'exec')

        # Prepare the restricted execution environment
        restricted_globals = safe_globals.copy()
        restricted_globals.update({
            'BaseRunnable': BaseRunnable,
            '__metaclass__': type,
            '__name__': '__main__',
            '__file__': '<string>',
            '_write_': full_write_guard,  # allow writes
            '_getattr_': safer_getattr,  # allow gets
            '_getitem_': default_guarded_getitem,
            '_getiter_': default_guarded_getiter,
            '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
            '_setattr_': guarded_setattr,
            'requests': requests,  # Allow 'requests' module
            'List': List,
            'Dict': Dict,
            **utility_builtins
        })

        # Execute the restricted code
        exec(compiled_code, restricted_globals)

        # Access the newly created class from the restricted globals
        runnable_class = restricted_globals['Runnable']

        # Instantiate the new class of type Runnable locally named runnable_class
        runnable = runnable_class(
            output_state=self.output_state,
            storage=self.storage
        )

        runnable.init()

        # return the runnable instance of the class
        return runnable

    @property
    def template(self):
        if self.config.template_id:
            template = self.storage.fetch_template(self.config.template_id)
            return template.template_content
        return None

    # TODO remove once core is reinstalled
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.runnable = self.create_runnable_class_instance()

    @property
    def config(self) -> StateConfigCode:
        return self.output_state.config

    async def process_input_data_entry(self, input_query_state: dict, force: bool = False):
        output_query_states = self.runnable.process_query_states(query_states=[input_query_state])
        return self.apply_states(output_query_states)

    def apply_states(self, query_states: [dict]):
        route_message = {
            "provider_id": self.provider.id,
            "processor_id": self.processor.id,
            "state_id": self.output_state.id,
            "type": "query_state_list",
            "query_state_list": query_states
        }

        self.sync_store_route.send_message(json.dumps(route_message))
