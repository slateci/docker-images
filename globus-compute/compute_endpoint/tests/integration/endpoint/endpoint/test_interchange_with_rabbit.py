from __future__ import annotations

import multiprocessing
import time
import uuid
import warnings

import dill
import pika
import pytest
from globus_compute_common.messagepack import pack
from globus_compute_common.messagepack.message_types import Result, Task
from globus_compute_endpoint.endpoint.interchange import EndpointInterchange
from globus_compute_endpoint.endpoint.utils.config import Config
from tests.integration.endpoint.executors.mock_executors import MockExecutor
from tests.utils import try_for_timeout


@pytest.fixture
def run_interchange_process(
    get_standard_compute_client, setup_register_endpoint_response, tmp_path
):
    """
    Start and stop a subprocess that executes the EndpointInterchange class.

    Yields a tuple of the interchange subprocess, (temporary) working directory,
    a random endpoint id, and the mocked registration info.
    """

    def run_it(reg_info: dict, endpoint_uuid, endpoint_dir):
        mock_exe = MockExecutor()
        mock_exe.endpoint_id = endpoint_uuid

        config = Config(executors=[mock_exe])

        ix = EndpointInterchange(
            config=config,
            endpoint_id=endpoint_uuid,
            reg_info=reg_info,
            endpoint_dir=endpoint_dir,
        )

        ix.start()

    endpoint_uuid = str(uuid.uuid4())
    endpoint_name = "endpoint_foo"
    gcc = get_standard_compute_client()
    setup_register_endpoint_response(endpoint_uuid)
    reg_info = gcc.register_endpoint(endpoint_name, endpoint_uuid)
    assert isinstance(reg_info, dict), "Test setup verification"
    assert reg_info["endpoint_id"] == endpoint_uuid, "Test setup verification"
    assert "task_queue_info" in reg_info
    assert "result_queue_info" in reg_info

    ix_proc = multiprocessing.Process(
        target=run_it, args=(reg_info, endpoint_uuid), kwargs={"endpoint_dir": tmp_path}
    )
    ix_proc.start()

    yield ix_proc, tmp_path, endpoint_uuid, reg_info

    if ix_proc.is_alive():
        ix_proc.terminate()
        try_for_timeout(lambda: not ix_proc.is_alive())

    rc = ix_proc.exitcode
    if rc is not None and rc != 0:
        warnings.warn(f"Interchange process exited with nonzero result code: {rc}")

    if rc is None:
        warnings.warn("Interchange process did not shut down cleanly - send SIGKILL")
        ix_proc.kill()


def test_epi_graceful_shutdown(run_interchange_process):
    ix_proc, tmp_path, endpoint_uuid, _reg_info = run_interchange_process
    time.sleep(2)  # simple test approach for now: assume it's up after 2s
    ix_proc.terminate()
    assert try_for_timeout(lambda: ix_proc.exitcode is not None), "Failed to shutdown"


def test_epi_stored_results_processed(run_interchange_process):
    ix_proc, tmp_path, endpoint_uuid, _reg_info = run_interchange_process

    unacked_results_dir = tmp_path / "unacked_results"
    unacked_results_dir.mkdir(exist_ok=True)
    stored_task_name = str(uuid.uuid4())
    stored_task_path = unacked_results_dir / stored_task_name
    stored_task_path.write_bytes(b"GIBBERISH")

    def file_is_gone():
        return not stored_task_path.exists()

    assert try_for_timeout(file_is_gone), "Expected stored task to be handled"


def test_epi_forwards_tasks_and_results(
    run_interchange_process, pika_conn_params, randomstring
):
    """
    Verify the two main threads of kernel interest: that tasks are pulled from the
    appropriate queue, and results are put into appropriate queue with the correct
    routing_key.
    """
    ix_proc, tmp_path, endpoint_uuid, reg_info = run_interchange_process

    task_uuid = uuid.uuid4()
    task_msg = Task(task_id=task_uuid, task_buffer=randomstring())

    task_q, res_q = reg_info["task_queue_info"], reg_info["result_queue_info"]
    res_q_name = res_q["queue"]
    task_q_name = task_q["queue"]
    task_exch = task_q["exchange"]
    with pika.BlockingConnection(pika_conn_params) as mq_conn:
        with mq_conn.channel() as chan:
            chan.queue_purge(task_q_name)
            chan.queue_purge(res_q_name)
            # publish our canary task
            chan.basic_publish(task_exch, task_q_name, pack(task_msg))

            # then get (consume) our expected result
            result: Result | None = None
            for mframe, mprops, mbody in chan.consume(
                queue=res_q_name, inactivity_timeout=5
            ):
                assert (mframe, mprops, mbody) != (None, None, None), "no timely result"
                result = dill.loads(mbody)
                break
    assert result is not None
    assert result.task_id == task_uuid
    assert result.data == task_msg.task_buffer
