








def application(environ,start_response):
    if environ["REQUEST_METHOD"] == "GET":  # 判断请求方法是否是GET
        start_response('200 OK',[('Content-Type', 'text/html')])  # 回调
        return [b'Hello World'] # 返回一个可迭代对象

from wsgiref.simple_server import make_server
httpd=make_server('127.0.0.1',port=9005,app=application)

if __name__ == "__main__":
    httpd.serve_forever()