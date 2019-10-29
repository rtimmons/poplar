from collections import namedtuple

import client.metrics_pb2_grpc as metrics
import client.recorder_pb2_grpc as recorder
import client.recorder_pb2 as recorder2
import client.poplar_pb2 as poplar

import google.protobuf.duration_pb2 as gduration
import google.protobuf.json_format as js

import collections

import grpc

Event = collections.namedtuple('Event', ['TotalSeconds', 'TotalNanos', 'Seconds', 'Nanos', 'Size', 'Ops'])

NAME = "InsertRemove.Insert"


def create_collector():
    channel = grpc.insecure_channel('localhost:2288')
    collector = recorder.PoplarMetricsRecorderStub(channel)

    options = poplar.CreateOptions()
    options.name = NAME
    options.path = "t1"
    options.chunkSize = 10
    options.streaming = True
    options.dynamic = False
    options.recorder = poplar.CreateOptions.RecorderType.PERF

    response = collector.CreateRecorder(options)
    assert response.status

    poplar_id = poplar.PoplarID()
    poplar_id.name = NAME

    return collector, poplar_id


def end_collector(collector, poplar_id):
    response = collector.CloseRecorder(poplar_id)
    assert response.status


def send_event(collector, poplar_id, event):

    response = collector.BeginEvent(poplar_id)
    assert response.status

    duration = recorder2.EventSendDuration()
    duration.duration.seconds = 1  # event.Seconds
    duration.duration.nanos = 23434  # event.Nanos
    duration.name = NAME

    response = collector.SetDuration(duration)
    assert response.status

    duration = recorder2.EventSendDuration()
    duration.duration.seconds = 1  # event.TotalSeconds
    duration.duration.nanos = 23434  # event.TotalNanos
    duration.name = NAME

    response = collector.SetTotalDuration(duration)
    assert response.status

    send_int = recorder2.EventSendInt()
    send_int.name = NAME
    send_int.value = 500  # event.Size
    response = collector.IncSize(send_int)
    assert response.status

    send_int.value = 1  # event.Ops
    response = collector.IncIterations(send_int)
    assert response.status

    response = collector.EndEvent(poplar_id)
    assert response.status


def main():
    collector, poplar_id = create_collector()
    # ['TotalSeconds', 'TotalNanos', 'Seconds', 'Nanos', 'Size', 'Ops']
    send_event(collector, poplar_id, Event(0, 150, 0, 100, 500, 1))
    end_collector(collector, poplar_id)


if __name__ == '__main__':
    main()
