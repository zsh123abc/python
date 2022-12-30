# -*- coding: utf-8 -*-

import socket
import re
import urllib.parse

def service_client(new_socket):
    # 为这个客户端返回数据
    # 1.接收浏览器发过来的请求，即http请求
    # GET / HTTP/1.1
    request = new_socket.recv(1024).decode('utf-8')
    request_header_lines = request.splitlines()
    ret = re.match(r'[^/]+(/[^ ]*)',request_header_lines[0])
    path_name = "/"
    if ret:
        path = ret.group(1) # 取出请求中的路径名
        path_name = urllib.parse.unquote(path) # 浏览器请求的路径中带有中文，会被自动编码，需要先解码成中文，才能找到后台中对应的html文件
        print("请求路径：{}".format(path_name))

    if path_name == "/":  # 用户请求/时，返回index.html页面
        path_name = "/index.html"
 
    # 2.返回http格式的数据给浏览器
    file_name = "D:\zsh\label_system_backend_python\zsh"+path_name
    try:
        f = open(file_name,'rb')
    except:
        response = "HTTP/1.1 404 NOT FOUND\r\n"
        response += "\r\n"
        response += "------file not found------"
        new_socket.send(response.encode("utf-8"))
    else:
        html_content = f.read()
        f.close()
        # 准备发给浏览器的数据 -- header
        response = "HTTP/1.1 200 OK\r\n"
        response += "\r\n"
        new_socket.send(response.encode("utf-8"))
        new_socket.send(html_content)    
    # 关闭套接字
    new_socket.close()


def main():
    # 用来完成整体的控制
    # 1.创建套接字
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 设置当服务器先close 即服务器端4次挥手之后资源能够立即释放，这样就保证了，下次运行程序时 可以立即绑定7788端口
    tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 2.绑定
    tcp_server_socket.bind(("",8100))    
    # 3.变为监听套接字
    tcp_server_socket.listen(128)
    
    while True:
        # 4.等待新客户端的链接
        new_socket, client_addr = tcp_server_socket.accept()       
        # 5.为这个客户端服务
        service_client(new_socket)
        
    # 关闭监听套接字
    tcp_server_socket.close()
        
if __name__ == '__main__':
    main()
