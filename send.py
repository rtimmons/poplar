import client.metrics_pb2_grpc as metrics
import client.recorder_pb2_grpc as recorder
import client.recorder_pb2 as recorder2
import client.poplar_pb2 as poplar

import google.protobuf.duration_pb2 as gduration
import google.protobuf.json_format as js

import grpc


def main():
    channel = grpc.insecure_channel('localhost:2288')
    collector = recorder.PoplarMetricsRecorderStub(channel)

    """
    message CreateOptions {
  string name = 1;
  string path = 2;
  int32 chunkSize = 3;
  bool streaming = 4;
  bool dynamic = 5;
  enum RecorderType {
    UNKNOWN = 0;
    PERF = 1;
    PERF_SINGLE = 2;
    PERF_100MS = 3;
    PERF_1S = 4;
    HISTOGRAM_SINGLE = 6;
    HISTOGRAM_100MS = 7;
    HISTOGRAM_1S = 8;
    INTERVAL_SUMMARIZATION = 9;
  };
  RecorderType recorder = 6;
    """
    options = poplar.CreateOptions()
    options.name = "InsertRemove.Insert"
    options.path = "t1"
    options.chunkSize = 10
    options.streaming = True
    options.dynamic = False
    options.recorder = poplar.CreateOptions.RecorderType.PERF

    response = collector.CreateRecorder(options)
    assert response.status

    poplar_id = poplar.PoplarID()
    poplar_id.name = response.name

    response = collector.BeginEvent(poplar_id)
    assert response.status

    duration = recorder2.EventSendDuration()
    duration.duration.seconds = 1
    duration.duration.nanos = 23434
    duration.name = options.name

    response = collector.SetDuration(duration)
    assert response.status

    duration = recorder2.EventSendDuration()
    duration.duration.seconds = 1
    duration.duration.nanos = 23434
    duration.name = options.name

    response = collector.SetTotalDuration(duration)
    assert response.status

    send_int = recorder2.EventSendInt()
    send_int.name = options.name
    send_int.value = 500
    response = collector.IncSize(send_int)
    assert response.status

    send_int.value = 1
    response = collector.IncIterations(send_int)
    assert response.status

    response = collector.EndEvent(poplar_id)
    assert response.status

    response = collector.CloseRecorder(poplar_id)
    assert response.status


if __name__ == '__main__':
    main()
