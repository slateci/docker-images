from __future__ import annotations

import multiprocessing
import os
import random
import string

# multiprocessing.Event is a method, not a class
# to annotate, we need the "real" class
# see: https://github.com/python/typeshed/issues/4266
from multiprocessing.synchronize import Event as EventType

import pika
import pika.exceptions
import pytest
from globus_compute_endpoint.endpoint.rabbit_mq import (
    RabbitPublisherStatus,
    ResultQueuePublisher,
    TaskQueueSubscriber,
)
from pika.exchange_type import ExchangeType
from tests.integration.test_rabbit_mq.result_queue_subscriber import (
    ResultQueueSubscriber,
)
from tests.integration.test_rabbit_mq.task_queue_publisher import TaskQueuePublisher


@pytest.fixture(scope="session")
def rabbitmq_conn_url():
    env_var_name = "RABBITMQ_INTEGRATION_TEST_URI"
    rmq_test_uri = os.getenv(env_var_name, "amqp:///")

    try:
        # Die here and now, first thing, with a hopefully-helpful direct fix suggestion
        # if rmq_test_uri is invalid or otherwise "not working."
        pika.BlockingConnection(pika.URLParameters(rmq_test_uri))
    except Exception as exc:
        msg = (
            f"Failed to connect to RabbitMQ via URI: {rmq_test_uri}\n"
            f"  Do you need to export {env_var_name} ?  Typo?"
        )
        raise ValueError(msg) from exc

    return rmq_test_uri


@pytest.fixture(scope="session")
def pika_conn_params(rabbitmq_conn_url):
    return pika.URLParameters(rabbitmq_conn_url)


def _flush_results(pika_conn_params):
    """Reminder: not a fixture; regular method"""
    with pika.BlockingConnection(pika_conn_params) as mq_conn:
        with mq_conn.channel() as chan:
            queue_name = "results"
            chan.exchange_declare(
                exchange="results",
                exchange_type="topic",
                durable=True,
            )
            chan.queue_declare(queue=queue_name, durable=True)
            chan.queue_purge(queue=queue_name)


@pytest.fixture
def flush_results(pika_conn_params):
    _flush_results(pika_conn_params)


@pytest.fixture(scope="session", autouse=True)
def clear_results_queue(pika_conn_params):
    _flush_results(pika_conn_params)
    yield
    _flush_results(pika_conn_params)


@pytest.fixture
def create_result_queue_info(rabbitmq_conn_url, tod_session_num, request):
    def _do_it(connection_url=None, queue_id=None) -> dict:
        exchange_name = "results"
        if not queue_id:
            queue_id = f"test_result_queue_{tod_session_num}__{request.node.name}"
        if not connection_url:
            connection_url = rabbitmq_conn_url
        routing_key = f"{queue_id}.results"
        return {
            "connection_url": connection_url,
            "exchange": exchange_name,
            "queue": "results",
            "queue_publish_kwargs": {
                "exchange": exchange_name,
                "routing_key": routing_key,
                "mandatory": True,
                "properties": {
                    "delivery_mode": pika.spec.PERSISTENT_DELIVERY_MODE,
                },
            },
            "test_routing_key": queue_id,
        }

    return _do_it


@pytest.fixture
def result_queue_info(create_result_queue_info) -> dict:
    return create_result_queue_info()


@pytest.fixture
def task_queue_info(rabbitmq_conn_url, tod_session_num, request) -> dict:
    queue_id = f"test_task_queue_{tod_session_num}__{request.node.name}"
    return {
        "connection_url": rabbitmq_conn_url,
        "exchange": "tasks",
        "queue": f"{queue_id}.tasks",
        "test_routing_key": queue_id,
    }


@pytest.fixture
def running_subscribers(request):
    run_list = []

    def cleanup():
        for x in run_list:
            try:  # cannot check is_alive on closed proc
                is_alive = x.is_alive()
            except ValueError:
                is_alive = False
            if is_alive:
                try:
                    x.stop()
                except Exception as e:
                    x.terminate()
                    raise Exception(
                        f"{x.__class__.__name__} did not shutdown correctly"
                    ) from e

    request.addfinalizer(cleanup)
    return run_list


@pytest.fixture(scope="session")
def ensure_result_queue(pika_conn_params):
    queues_created = []

    def _do_ensure(exchange_opts=None, queue_opts=None):
        if not exchange_opts:
            exchange_opts = {
                "exchange": "results",
                "exchange_type": ExchangeType.topic.value,
                "durable": True,
            }
        if not queue_opts:
            queue_opts = {"queue": "results", "durable": True}
            routing_key = "*.results"
        else:
            routing_key = queue_opts["queue"]

        with pika.BlockingConnection(pika_conn_params) as mq_conn:
            with mq_conn.channel() as chan:
                chan.exchange_declare(**exchange_opts)
                chan.queue_declare(**queue_opts)
                queues_created.append(queue_opts["queue"])
                chan.queue_bind(
                    queue=queue_opts["queue"],
                    exchange=exchange_opts["exchange"],
                    routing_key=routing_key,
                )

    _do_ensure()  # The main "results" should always exist for our tests
    yield _do_ensure

    with pika.BlockingConnection(pika_conn_params) as mq_conn:
        with mq_conn.channel() as chan:
            for q_name in queues_created:
                chan.queue_delete(q_name)


@pytest.fixture
def start_task_q_subscriber(
    running_subscribers,
    task_queue_info,
    default_endpoint_id,
    ensure_task_queue,
):
    def func(
        *,
        endpoint_id: str | None = None,
        queue: multiprocessing.Queue | None = None,
        quiesce_event: EventType | None = None,
        override_params: pika.connection.Parameters | None = None,
    ):
        if endpoint_id is None:
            endpoint_id = default_endpoint_id
        if quiesce_event is None:
            quiesce_event = multiprocessing.Event()
        if queue is None:
            queue = multiprocessing.Queue()
        q_info = task_queue_info if override_params is None else override_params
        ensure_task_queue(queue_opts={"queue": q_info["queue"]})

        task_q = TaskQueueSubscriber(
            queue_info=q_info,
            external_queue=queue,
            quiesce_event=quiesce_event,
            endpoint_id=endpoint_id,
        )
        task_q.start()
        running_subscribers.append(task_q)
        return task_q

    return func


@pytest.fixture
def start_result_q_subscriber(running_subscribers, pika_conn_params):
    def func(
        *,
        queue: multiprocessing.Queue | None = None,
        kill_event: multiprocessing.Event | None = None,
        override_params: pika.connection.Parameters | None = None,
    ):
        if kill_event is None:
            kill_event = multiprocessing.Event()
        if queue is None:
            queue = multiprocessing.Queue()
        result_q = ResultQueueSubscriber(
            conn_params=pika_conn_params if not override_params else override_params,
            external_queue=queue,
            kill_event=kill_event,
        )
        result_q.start()
        running_subscribers.append(result_q)
        if not result_q.test_class_ready.wait(10):
            raise AssertionError("Result Queue subscriber failed to initialize")
        return result_q

    return func


@pytest.fixture
def running_publishers(request):
    run_list = []

    def cleanup():
        for x in run_list:
            if x.status is RabbitPublisherStatus.connected:
                x.close()

    request.addfinalizer(cleanup)
    return run_list


@pytest.fixture
def start_result_q_publisher(
    running_publishers,
    result_queue_info,
    ensure_result_queue,
):
    def func(
        *,
        override_params: dict | None = None,
        queue_purge: bool = True,
    ):
        q_info = result_queue_info if override_params is None else override_params
        exchange_name, queue_name = q_info.get("exchange"), q_info.get("queue")
        if exchange_name:  # We'll call it an error to specify only one
            exchange_opts = {
                "exchange": exchange_name,
                "exchange_type": ExchangeType.topic.value,
                "durable": True,
            }
            queue_opts = {"queue": queue_name, "durable": True}
            ensure_result_queue(exchange_opts=exchange_opts, queue_opts=queue_opts)

        result_pub = ResultQueuePublisher(queue_info=q_info)
        result_pub.connect()
        if queue_purge:  # Make sure queue is empty
            result_pub._channel.queue_purge(q_info["queue"])
        running_publishers.append(result_pub)
        return result_pub

    return func


@pytest.fixture
def start_task_q_publisher(
    running_publishers,
    task_queue_info,
    ensure_task_queue,
    default_endpoint_id,
):
    def func(
        *,
        override_params: pika.connection.Parameters | None = None,
        queue_purge: bool = True,
    ):
        q_info = task_queue_info if override_params is None else override_params
        exchange_name, queue_name = q_info.get("exchange"), q_info.get("queue")
        if exchange_name:  # We'll call it an error to specify only one
            exchange_opts = {
                "exchange": exchange_name,
                "exchange_type": ExchangeType.direct.value,
            }
            queue_opts = {"queue": queue_name, "arguments": {"x-expires": 30 * 1000}}
            ensure_task_queue(exchange_opts=exchange_opts, queue_opts=queue_opts)

        task_pub = TaskQueuePublisher(queue_info=q_info)
        task_pub.connect()
        if queue_purge:  # Make sure queue is empty
            task_pub._channel.queue_purge(q_info["queue"])
        running_publishers.append(task_pub)
        return task_pub

    return func


@pytest.fixture(scope="session")
def ensure_task_queue(pika_conn_params, tod_session_num, request):
    queues_created = []

    def _do_ensure(exchange_opts=None, queue_opts=None):
        if not exchange_opts:
            exchange_opts = {
                "exchange": "tasks",
                "exchange_type": ExchangeType.direct.value,
            }
        exchange_opts.setdefault("durable", True)
        if not queue_opts:
            rndm = "".join(random.choice(string.ascii_letters) for _ in range(5))
            queue_id = f"queue_{tod_session_num}__{request.node.name}__{rndm}"
            queue_opts = {"queue": f"task_{queue_id}.tasks"}
        # play nice with dev/test resources; auto clean
        queue_opts.setdefault("arguments", {"x-expires": 30 * 1000})

        with pika.BlockingConnection(pika_conn_params) as mq_conn:
            with mq_conn.channel() as chan:
                chan.exchange_declare(**exchange_opts)
                chan.queue_declare(**queue_opts)
                queues_created.append(queue_opts["queue"])
                chan.queue_bind(
                    queue=queue_opts["queue"],
                    exchange=exchange_opts["exchange"],
                    routing_key=queue_opts["queue"],
                )

    yield _do_ensure

    with pika.BlockingConnection(pika_conn_params) as mq_conn:
        with mq_conn.channel() as chan:
            for q_name in queues_created:
                chan.queue_delete(q_name)
