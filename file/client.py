import grpc
import file.compute_pb2
import file.compute_pb2_grpc

_HOST = '192.168.100.98'
_PORT = '10053'

def skeleton_calculate(path, userFileIds):
    # with grpc.insecure_channel('{}:{}'.format(_HOST, _PORT)) as channel:
    # 连接 rpc 服务器，ip和端口号必须和服务端设置的一致
    # with 离开语句时会自动调用释放资源方法，as 起别名
    with grpc.insecure_channel('{}:{}'.format(_HOST,_PORT)) as channel:
        # 调用 rpc 服务
        client = file.compute_pb2_grpc.ComputeStub(channel=channel)
        #response = client.SayHello(compute_pb2.HelloRequest(helloworld='12345678'))
        response = client.skeleton_calculate(file.compute_pb2.skeletonRequest(skeleton=path, skeleton_id=userFileIds))
    #print('received:' + response.result)

    return response
