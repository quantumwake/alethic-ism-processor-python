from typing import Any
import dotenv
from ismcore.compiler.secure_runnable import SecurityConfig, SecureRunnableBuilder
from ismcore.model.processor_state import StateConfigCode
from ismcore.processor.base_processor import BaseProcessor
from ismcore.processor.monitored_processor_state import MonitoredUsage

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

    async def process_input_data(self, input_data: dict, force: bool = False):
        if isinstance(input_data, dict):
            input_data = [input_data]

        output_query_states = self.runnable.process(queries=input_data)
        await self.finalize_result(
            input_data=input_data,
            result=output_query_states,
            additional_query_state=None
        )

    async def _stream(self, input_data: Any, template: str):
        # Iterate through the synchronous generator
        for data in self.runnable.process_stream(input_data):
            # Yield the data asynchronously
            yield data
