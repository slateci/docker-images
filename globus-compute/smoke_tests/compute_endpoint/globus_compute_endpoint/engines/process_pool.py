from __future__ import annotations

import logging
import multiprocessing
import typing as t
import uuid
from concurrent.futures import Future
from concurrent.futures import ProcessPoolExecutor as NativeExecutor
from multiprocessing.queues import Queue as mpQueue

import psutil
from globus_compute_common.messagepack.message_types import (
    EPStatusReport,
    TaskTransition,
)
from globus_compute_endpoint.engines.base import (
    GlobusComputeEngineBase,
    ReportingThread,
)

logger = logging.getLogger(__name__)


class ProcessPoolEngine(GlobusComputeEngineBase):
    def __init__(
        self,
        *args,
        label: str = "ProcessPoolEngine",
        heartbeat_period_s: float = 30.0,
        **kwargs,
    ):
        self.label = label
        self.executor = NativeExecutor(*args, **kwargs)
        self._status_report_thread = ReportingThread(
            target=self.report_status, args=[], reporting_period=heartbeat_period_s
        )
        super().__init__(*args, heartbeat_period_s=heartbeat_period_s, **kwargs)

    def start(
        self,
        *args,
        endpoint_id: t.Optional[uuid.UUID] = None,
        results_passthrough: t.Optional[mpQueue] = None,
        **kwargs,
    ) -> None:
        """
        Parameters
        ----------
        endpoint_id: Endpoint UUID
        results_passthrough: Queue to which packed results will be posted
        run_dir Not used
        Returns
        -------
        """
        assert endpoint_id, "ProcessPoolExecutor requires kwarg:endpoint_id at start"
        self.endpoint_id = endpoint_id
        if results_passthrough:
            self.results_passthrough = results_passthrough
        assert self.results_passthrough

        # mypy think the thread can be none
        self._status_report_thread.start()

    def get_status_report(self) -> EPStatusReport:
        """
        endpoint_id: uuid.UUID
        ep_status_report: t.Dict[str, t.Any]
        task_statuses: t.Dict[str, t.List[TaskTransition]]
        Returns
        -------
        """
        executor_status: t.Dict[str, t.Any] = {
            "task_id": -2,
            "info": {
                "total_cores": multiprocessing.cpu_count(),
                "total_mem": round(psutil.virtual_memory().available / (2**30), 1),
                "total_core_hrs": 0,
                "total_workers": self.executor._max_workers,  # type: ignore
                "pending_tasks": 0,
                "outstanding_tasks": 0,
                "scaling_enabled": False,
                "max_blocks": 1,
                "min_blocks": 1,
                "max_workers_per_node": self.executor._max_workers,  # type: ignore
                "nodes_per_block": 1,
                "heartbeat_period": self._heartbeat_period_s,
            },
        }
        task_status_deltas: t.Dict[str, t.List[TaskTransition]] = {}

        return EPStatusReport(
            endpoint_id=self.endpoint_id,
            ep_status_report=executor_status,
            task_statuses=task_status_deltas,
        )

    def _submit(
        self,
        func: t.Callable,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> Future:
        """We basically pass all params except the resource_specification
        over to executor.submit
        """
        logger.warning("Got task")
        return self.executor.submit(func, *args, **kwargs)

    def status_polling_interval(self) -> int:
        return 30

    def scale_out(self, blocks: int) -> list[str]:
        return []

    def scale_in(self, blocks: int) -> list[str]:
        return []

    def status(self) -> dict:
        return {}

    def shutdown(self):
        self._status_report_thread.stop()
        self.executor.shutdown()
