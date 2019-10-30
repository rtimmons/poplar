import client.collector_pb2_grpc as pcollector
import client.collector_pb2 as collector_model
import client.poplar_pb2 as poplar

import google.protobuf.json_format as f

import collections

import grpc
import bson
import random
import threading
from datetime import datetime

Event = collections.namedtuple('Event', ['TotalSeconds', 'TotalNanos', 'Seconds', 'Nanos', 'Size', 'Ops'])

NAME = "InsertRemove.Insert"
THREADS = 10
HOW_MANY_EVENTS = 100 * 1000 / THREADS
ALL_FIELDS = True


def create_collector():
    channel = grpc.insecure_channel('localhost:2288')
    collector = pcollector.PoplarEventCollectorStub(channel)

    options = poplar.CreateOptions()
    options.name = NAME
    options.path = "t1"
    options.chunkSize = 10000
    options.streaming = True
    options.dynamic = False
    options.recorder = poplar.CreateOptions.RecorderType.PERF

    try:
        response = collector.CreateCollector(options)
        assert response.status
    except Exception as e:
        # if we've already tried running this thing
        print(e)
        pass

    poplar_id = poplar.PoplarID()
    poplar_id.name = NAME

    return collector, poplar_id


def end_collector(collector, poplar_id):
    response = collector.CloseCollector(poplar_id)
    assert response.status


def to_metrics_event(event):
    # convert Event namedtuple to EventMetrics (dummy/hard-coded numbers for now)
    metrics = collector_model.EventMetrics()
    metrics.name = NAME
    metrics.time.seconds = 1572450055062
    metrics.time.nanos = 247

    metrics.timers.total.seconds = 1
    metrics.timers.total.nanos = 500
    metrics.timers.duration.seconds = 0
    metrics.timers.duration.nanos = 10000000

    metrics.counters.size = 20
    metrics.counters.ops = 1
    metrics.counters.number = 1

    # what is guages.state?
    metrics.gauges.state = 1
    # threads don't know this value
    metrics.gauges.workers = 1
    metrics.gauges.failed = 0

    return metrics


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
    threads = []
    start = datetime.now()
    for _ in range(THREADS):
        thread = threading.Thread(target=run_poplar_main_thread, args=(collector, poplar_id))
        threads.append(thread)
        thread.run()
    for thread in threads:
        try:
            thread.join()
        except Exception as e:
            pass
    end = datetime.now()
    print("Took %i seconds for %i threads to write %i events" % ((end - start).total_seconds(), THREADS, HOW_MANY_EVENTS * THREADS))
    end_collector(collector, poplar_id)


def run_poplar_main_thread(collector, poplar_id):
    events = random_events()
    start = datetime.now()
    for event in events:
        # ideally would call
        #     collector.StreamEvents([to_event(event) for event in events])
        # but that doesn't work
        response = collector.SendEvent(to_metrics_event(event))
        assert response.status
    end = datetime.now()
    print("Took %i seconds for poplar to write %i events" % ((end - start).total_seconds(), HOW_MANY_EVENTS))


if __name__ == '__main__':
    # bson_encoded_main()
    # bson_main()
    poplar_main()
