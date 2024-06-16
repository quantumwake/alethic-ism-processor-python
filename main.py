import json
import os
import dotenv
from core.base_message_consumer_state import BaseMessagingConsumerState
from core.base_message_router import Router
from core.base_model import ProcessorProvider, Processor, ProcessorState
from core.processor_state import State
from core.pulsar_message_producer_provider import PulsarMessagingProducerProvider
from core.pulsar_messaging_provider import PulsarMessagingConsumerProvider
from db.processor_state_db_storage import PostgresDatabaseStorage

from processor_python import PythonProcessor

dotenv.load_dotenv()
MSG_URL = os.environ.get("MSG_URL", "pulsar://localhost:6650")
MSG_TOPIC = os.environ.get("MSG_TOPIC", "ism_python_executor")
MSG_MANAGE_TOPIC = os.environ.get("MSG_MANAGE_TOPIC", "ism_python_executor_manage_topic")
MSG_TOPIC_SUBSCRIPTION = os.environ.get("MSG_TOPIC_SUBSCRIPTION", "ism_python_executor_subscription")

# database related
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres1@localhost:5432/postgres")

# Message Routing File (
#   The responsibility of this state sync store is to take inputs and
#   store them into a consistent state storage class. After, the intent is
#   to automatically route the newly synced data to the next state processing unit
#   route them to the appropriate destination, as defined by the
#   route selector
# )
ROUTING_FILE = os.environ.get("ROUTING_FILE", '.routing.yaml')
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# state storage specifically to handle this processor state (stateless obj)
storage = PostgresDatabaseStorage(
    database_url=DATABASE_URL,
    incremental=True
)

messaging_provider = PulsarMessagingConsumerProvider(
    message_url=MSG_URL,
    message_topic=MSG_TOPIC,
    message_topic_subscription=MSG_TOPIC_SUBSCRIPTION,
    management_topic=MSG_MANAGE_TOPIC
)


# routing the persistence of individual state entries to the state sync store topic
pulsar_router_provider = PulsarMessagingProducerProvider()
router = Router(
    provider=pulsar_router_provider,
    yaml_file=ROUTING_FILE
)

# find the monitor route for telemetry updates
monitor_route = router.find_router("processor/monitor")
state_router_route = router.find_router("processor/monitor")
sync_store_route = router.find_router('state/sync/store')


class MessagingConsumerPython(BaseMessagingConsumerState):

    def create_processor(self,
                         processor: Processor,
                         provider: ProcessorProvider,
                         output_processor_state: ProcessorState,
                         output_state: State):

        processor = PythonProcessor(
            # storage class information
            state_machine_storage=storage,

            # state processing information
            output_state=output_state,
            provider=provider,
            processor=processor,
            output_processor_state=output_processor_state,

            # state information routing routers
            monitor_route=self.monitor_route,
            state_router_route=state_router_route,
            sync_store_route=sync_store_route
        )

        return processor

    # async def execute(self, message: dict):
    #     await super().execute(message)


if __name__ == '__main__':
    consumer = MessagingConsumerPython(
        name="MessagingConsumerPython",
        storage=storage,
        messaging_provider=messaging_provider,
        monitor_route=monitor_route
    )

    consumer.setup_shutdown_signal()
    consumer.start_topic_consumer()
