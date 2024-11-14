from typing import Any
import dotenv

from core.base_processor import BaseProcessor
from core.compiler.secure_runnable import SecureRunnableBuilder, SecurityConfig
from core.monitored_processor_state import MonitoredUsage
from core.processor_state import StateConfigCode

from logger import log

dotenv.load_dotenv()
logging = log.getLogger(__name__)


class PythonProcessor(BaseProcessor, MonitoredUsage):

    @property
    def template(self):
        if self.config.template_id:
            template = self.storage.fetch_template(self.config.template_id)
            return template

        return None

    # TODO remove once core is reinstalled
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.runnable = self.create_runnable_class_instance()

    def create_runnable_class_instance(self):
        user_code = self.template.template_content

        if not user_code:
            raise ValueError(f'unable execute blank user code for state route id: {self.output_processor_state.id}')

        # Create builder configuration context
        config = SecurityConfig(
            max_memory_mb=100,
            max_cpu_time_seconds=5,
            max_requests=50,
            allowed_domains=["*"],
            execution_timeout=10,
            enable_resource_limits=False
        )

        try:
            # Create builder
            builder = SecureRunnableBuilder(config)

            # Compile and instantiate the runnable
            return builder.compile(user_code)
        except Exception as e:
            print(f"Error: {str(e)}")

    @property
    def config(self) -> StateConfigCode:
        return self.output_state.config

    async def process_input_data_entry(self, input_query_state: dict, force: bool = False):
        output_query_states = self.runnable.process(queries=[input_query_state])
        await self.finalize_result(
            input_query_state=input_query_state,
            result=output_query_states,
            additional_query_state=None
        )

    async def _stream(self, input_data: Any, template: str):
        # Iterate through the synchronous generator
        for data in self.runnable.process_stream(input_data):
            # Yield the data asynchronously
            yield data

    #
    # async def apply_states(self, query_states: [dict]):
    #     route_message = {
    #         "route_id": self.output_processor_state.id,
    #         "type": "query_state_list",
    #         "query_state_list": query_states
    #     }
    #
    #     await self.sync_store_route.(json.dumps(route_message))
