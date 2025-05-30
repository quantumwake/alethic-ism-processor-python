import asyncio
import os
import dotenv

from ismcore.messaging.base_message_consumer_processor import BaseMessageConsumerProcessor
from ismcore.messaging.base_message_router import Router
from ismcore.messaging.nats_message_provider import NATSMessageProvider
from ismcore.model.base_model import Processor, ProcessorProvider, ProcessorState
from ismcore.model.processor_state import State
from ismcore.processor.base_processor import (
    StatePropagationProviderDistributor,
    StatePropagationProviderRouterStateSyncStore,
    StatePropagationProviderRouterStateRouter)
from ismcore.utils.ism_logger import ism_logger
from ismdb.postgres_storage_class import PostgresDatabaseStorage
from processor_python import PythonProcessor

dotenv.load_dotenv()

logging = ism_logger(__name__)

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

# state storage specifically to handle this processor state (stateless obj)
storage = PostgresDatabaseStorage(
    database_url=DATABASE_URL,
    incremental=True
)

# routing the persistence of individual state entries to the state sync store topic
message_provider = NATSMessageProvider()
router = Router(provider=message_provider, yaml_file=ROUTING_FILE)

# find the monitor route for telemetry updates
monitor_route = router.find_route("processor/monitor")
state_router_route = router.find_route("processor/state/router")
state_sync_route = router.find_route('processor/state/sync')
python_route_subscriber = router.find_route_by_subject("processor.executor.python")
state_stream_route = router.find_route("processor/state")
usage_route = router.find_route("processor/usage")

# state_router_route = router.find_router("processor/monitor")
state_propagation_provider = StatePropagationProviderDistributor(
    propagators=[
        StatePropagationProviderRouterStateSyncStore(route=state_sync_route),
        StatePropagationProviderRouterStateRouter(route=state_router_route, storage=storage)
    ]
)


class MessagingConsumerPython(BaseMessageConsumerProcessor):

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

            # stream outputs
            stream_route=state_stream_route,
            usage_route=usage_route,

            # state information routing routers
            monitor_route=self.monitor_route,
            state_propagation_provider=state_propagation_provider
        )

        return processor

    # async def execute(self, message: dict):
    #     await super().execute(message)


if __name__ == '__main__':
    consumer = MessagingConsumerPython(
        storage=storage,
        route=python_route_subscriber,
        monitor_route=monitor_route
    )

    consumer.setup_shutdown_signal()
    asyncio.get_event_loop().run_until_complete(consumer.start_consumer())
