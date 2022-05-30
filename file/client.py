import grpc
import file.compute_pb2
import file.compute_pb2_grpc

_HOST = '192.168.100.109'
_PORT = '10053'

def skeleton_calculate(path, userFileIds):
    # with grpc.insecure_channel('{}:{}'.format(_HOST, _PORT)) as channel:
    with grpc.insecure_channel('{}:{}'.format(_HOST,_PORT)) as channel:
        client = file.compute_pb2_grpc.ComputeStub(channel=channel)
        #response = client.SayHello(compute_pb2.HelloRequest(helloworld='12345678'))
        response = client.skeleton_calculate(file.compute_pb2.skeletonRequest(skeleton=path, skeleton_id=userFileIds))
    #print('received:' + response.result)
    
    return response
