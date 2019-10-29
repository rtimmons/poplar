import client.recorder_pb2_grpc as recorder
import client.recorder_pb2 as recorder2
import client.poplar_pb2 as poplar

import google.protobuf.json_format as f

import collections

import grpc
import bson
import random
from datetime import datetime

Event = collections.namedtuple('Event', ['TotalSeconds', 'TotalNanos', 'Seconds', 'Nanos', 'Size', 'Ops'])

NAME = "InsertRemove.Insert"
HOW_MANY_EVENTS = 1000 * 1000 * 10
ALL_FIELDS = True


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

    # response = collector.CreateRecorder(options)
    # assert response.status

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

    if ALL_FIELDS:
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

    response = collector.EndEvent(duration)
    assert response.status


def random_events():
    random.seed(1000)

    def random_event():
        return Event(random.randint(0, 5),
                     random.randint(0, 1000),
                     random.randint(0, 5),
                     random.randint(0, 1000),
                     random.randint(0, 500),
                     random.choice([0, 1]))

    return [random_event() for _ in range(HOW_MANY_EVENTS)]


def write_event(output, event):
    print(event)
    data = bson.encode_array([
        # ['TotalSeconds', 'TotalNanos', 'Seconds', 'Nanos', 'Size', 'Ops'])
        event.TotalSeconds,
        event.TotalNanos,
        event.Seconds,
        event.Nanos,
        event.Size,
        event.Ops
    ], [])
    output.write(data)


def bson_encoded_main():
    data = bson.encode_array([
        Event(TotalSeconds=3, TotalNanos=209, Seconds=3, Nanos=422, Size=157, Ops=0)
    ], [])
    start = datetime.now()
    with open('t1', 'wb+') as output:
        for _ in range(HOW_MANY_EVENTS):
            output.write(data)
    end = datetime.now()
    print("Took %i seconds for bson_encoded to write %i events" % ((end - start).seconds, HOW_MANY_EVENTS))


def bson_main():
    events = random_events()
    print(events[0])
    start = datetime.now()
    with open('t1', 'wb+') as output:
        for event in events:
            write_event(output, event)
    end = datetime.now()
    print("Took %i seconds for bson to write %i events" % ((end - start).total_seconds(), HOW_MANY_EVENTS))


def poplar_main():
    collector, poplar_id = create_collector()
    # ['TotalSeconds', 'TotalNanos', 'Seconds', 'Nanos', 'Size', 'Ops']
    events = random_events()
    start = datetime.now()
    for event in events:
        send_event(collector, poplar_id, event)
    end = datetime.now()
    end_collector(collector, poplar_id)
    print("Took %i seconds for poplar to write %i events" % ((end - start).total_seconds(), HOW_MANY_EVENTS))


if __name__ == '__main__':
    bson_encoded_main()
    # bson_main()
    # poplar_main()
